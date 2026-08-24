"""
chosuke_backend.py — Chosuke クラウド版ストレージバックエンド
============================================================
ローカルCSV/ファイル保存を、Googleスプレッドシート + Google Drive に置き換える層。

設計方針:
- app.py 側の業務ロジック(評点・原価率・セリフ等)は一切変更しない。
- app.py の load_*/save_*/append_* 関数は、このモジュールの関数に委譲するだけにする。
- 認証情報は Streamlit Secrets から読む(鍵JSONをコードやGitに置かない)。
- スプレッドシートのタブ(ワークシート)は、初回アクセス時に必要なものを自動生成する。
- スクショ画像は Drive フォルダにアップロードし、file_id を履歴に記録する。

必要な Secrets (Streamlit Cloud の Settings > Secrets に貼る / ローカルは .streamlit/secrets.toml):
    spreadsheet_id = "..."         # Chosuke_Data スプレッドシートのID
    drive_folder_id = "..."        # Chosuke_Screenshots フォルダのID
    staff_password = "..."         # staff 共通パスワード
    admin_password = "..."         # 管理者パスワード
    [gcp_service_account]          # 鍵JSONの中身をそのまま貼る
    type = "service_account"
    project_id = "..."
    ...
"""

import io
import json
import time

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ------------------------------------------------------------
# スコープ: Sheets と Drive の読み書き
# (Drive スコープは将来用に残すが、画像はスプレッドシートに保存する)
# ------------------------------------------------------------
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ------------------------------------------------------------
# 各タブ(ワークシート)の列定義。
# init_data() が無いタブを作るときのヘッダになる。
# 列の並び・名前は現行CSVと完全一致させる(業務ロジックがこの列名を参照するため)。
# ------------------------------------------------------------
SHEET_SCHEMAS = {
    "brands": [
        "brand_ja", "brand_en", "category",
        "cost_ratio_min", "cost_ratio_max", "notes", "iconic_models",
    ],
    "checklists": [
        "brand_ja", "category", "check_item", "hint",
    ],
    "feedback": [
        "timestamp", "staff", "brand_ja", "product_name",
        "feedback_type", "content", "promoted",
    ],
    "appraisal_history": [
        "timestamp", "staff", "brand_ja", "brand_en", "product_name", "year",
        "accessories", "rank", "price_min_usd", "price_max_usd",
        "screenshots_count", "notes",
        "actual_cost_rate", "yuhei_comment", "review_status", "reviewed_at", "tags",
        "category", "is_microchip", "is_year_unknown", "gc_status", "is_random_serial",
        # v0.13(クラウド): スクショの Drive file_id をカンマ区切りで保持。
        # これにより、従来のファイル名プレフィックス照合をやめ、確実な紐付けにする。
        "screenshot_ids",
    ],
    "keyword_requirements": [
        "brand_ja", "brand_en", "category",
        "keyword", "importance", "importance_label", "match_rule",
    ],
    "staff_master": [
        "staff_name",
    ],
    # v0.14: トレーニングモード(本格版)。
    #   staff が実際の商品画像(全体1枚+査定ポイント最大5枚)をアップし、
    #   自分の買取金額を入力して提出する。裕平さんが現物を見ながら4軸で評価する。
    #   画像は screenshots タブに shot_id(=この timestamp)で保存(査定モードと同じ方式)。
    "training_history": [
        "timestamp", "staff",
        # --- staff が入力する査定情報(査定モードと同じ項目) ---
        "brand_ja", "brand_en", "category", "product_name", "year",
        "accessories", "rank", "price_min_usd", "price_max_usd",
        "image_count",            # アップした画像枚数(全体1+査定ポイント最大5)
        "staff_offer_price",      # staff が出した自分の買取金額(本格版の肝)
        "screenshot_ids",         # 画像の shot_id(=timestamp)。screenshots タブ参照キー
        # --- 提出ステータス ---
        "review_status",          # pending / reviewed / skipped
        "submitted_at",
        # --- 裕平さんが入力する評価(現物を見ながら4軸) ---
        "eval_input",             # ①商品入力: 適切/要改善
        "eval_market_image",      # ②相場参考画像: 適切/要改善
        "eval_rank",              # ③Rank: 適切/要改善
        "expert_answer_min",      # ④正解の買取金額・下限(裕平さん)
        "expert_answer_max",      # ④正解の買取金額・上限(裕平さん)
        "expert_answer_price",    # (旧)単一値。後方互換のため残置
        "price_gap",              # staff_offer がレンジ外なら外れ幅、レンジ内なら0(自動計算)
        "overall_mark",           # 総合評価マーク: hanamaru / yoku / ganbaro
        "eval_comment",           # フィードバックコメント(自由記述)
        "expert_screenshot_ids",  # v0.15: 裕平さんが参考にした相場データ画像の shot_id
        "reviewed_at",
        "reviewed_by",            # v0.17: スキーマ整合(app.py が既に書き込んでいた列)
        "gap_band",               # v0.17: スキーマ整合(app.py が既に書き込んでいた列)
    ],
    # v0.17: 鑑定士試験レベル1
    "test_items": [
        "test_set_id",            # 問題セットの識別子。例 LV1-2026-09
        "q_no",                   # 問番号 1〜10
        "category",               # bag / shoes / apparel / jewellery / other
        "item_label",             # 管理者用の商品名メモ(受験者には非表示)
        "answer_min_usd",         # 正解相場の下限
        "answer_max_usd",         # 正解相場の上限
        "require_photo_id",       # 1=個体特定情報の撮影必須 / 0=免除
        "answer_rank",            # 参考用(採点しない)
        "answer_year",            # 参考用(採点しない)
        "notes",                  # 採点時の参照メモ
    ],
    "test_sessions": [
        "session_id",             # <test_set_id>::<staff>::<開始timestamp>
        "test_set_id",            # 問題セット
        "staff",                  # 受験者
        "started_at",             # 開始時刻
        "finished_at",            # 最終提出時刻
        "elapsed_min",            # 所要時間(分)。自動計算
        "status",                 # in_progress / submitted / graded / notified
        "total_score",            # 合計点(採点後に確定)
        "result",                 # pass / fail
        "graded_by",              # 採点者
        "graded_at",              # 採点日時
        "notified_at",            # 通知日時
    ],
    "test_answers": [
        "answer_id",              # <session_id>::<q_no>
        "session_id",             # 所属セッション
        "q_no",                   # 問番号
        "submitted_at",           # その問の提出時刻
        "shot_id",                # 画像の保存キー(screenshots タブ参照)
        "photo_overall",          # 全体像を提出したか 1/0
        "photo_logo",             # ロゴ 1/0
        "photo_id",               # 個体特定情報 1/0
        "photo_rank_count",       # Rankポイントの枚数
        "item_name",              # 商品名(採点しない)
        "year",                   # 年式(採点しない)
        "rank",                   # Rank(採点しない)
        "price_usd",              # 相場(数値ひとつ)
        "auto_photo_ok",          # 自動判定: 必須写真が揃っているか
        "auto_gap_rate",          # 自動判定: 乖離率(%)
        "auto_score",             # 自動判定: 10 / 5 / 0
        "final_score",            # 最終得点(既定は auto_score、Director が上書き可)
        "override_reason",        # 上書きした場合の理由
    ],
}


# ============================================================
# 認証・接続(キャッシュ)
# ============================================================
@st.cache_resource(show_spinner=False)
def _get_credentials() -> Credentials:
    """Secrets のサービスアカウント情報から認証情報を作る。"""
    sa_info = dict(st.secrets["gcp_service_account"])
    # secrets.toml に貼ると private_key の改行が \n 文字列になることがあるため正規化
    if "private_key" in sa_info:
        sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(sa_info, scopes=_SCOPES)


@st.cache_resource(show_spinner=False)
def _get_gspread_client() -> gspread.Client:
    return gspread.authorize(_get_credentials())


@st.cache_resource(show_spinner=False)
def _get_spreadsheet() -> gspread.Spreadsheet:
    sid = st.secrets["spreadsheet_id"]
    return _get_gspread_client().open_by_key(sid)


# ============================================================
# ワークシート取得・初期化
# ============================================================
_WS_CACHE = {}

def _get_or_create_ws(name: str) -> gspread.Worksheet:
    """名前付きワークシートを返す。無ければスキーマのヘッダ付きで作成する。
    ワークシートのハンドルはプロセス内でキャッシュし、毎回の metadata 取得を避ける。"""
    if name in _WS_CACHE:
        return _WS_CACHE[name]
    ss = _get_spreadsheet()
    try:
        ws = ss.worksheet(name)
    except gspread.WorksheetNotFound:
        header = SHEET_SCHEMAS.get(name, [])
        ws = ss.add_worksheet(title=name, rows=100, cols=max(len(header), 1))
        if header:
            ws.update([header], value_input_option="RAW")
    _WS_CACHE[name] = ws
    return ws


def init_backend():
    """全タブの存在を保証し、既存 appraisal_history に不足列があれば補う。
    現行 app.py の init_data() に相当(クラウド版)。
    ※API節約のため、セッション中に一度だけ実行する(2回目以降はスキップ)。"""
    if st.session_state.get("_backend_inited"):
        return
    # v0.17: 列の自動補完を複数タブに拡大(新規タブ追加時もここに足す)
    _MIGRATE_TABS = ["appraisal_history", "training_history", "feedback_items",
                     "test_items", "test_sessions", "test_answers"]
    for name in SHEET_SCHEMAS:
        ws = _get_or_create_ws(name)
        if name in _MIGRATE_TABS:
            _ensure_columns(ws, SHEET_SCHEMAS[name])
    st.session_state["_backend_inited"] = True


def _ensure_columns(ws: gspread.Worksheet, expected_cols: list):
    """ヘッダ行に不足列があれば末尾に追加する(既存データは保持)。"""
    existing = ws.row_values(1)
    missing = [c for c in expected_cols if c not in existing]
    if not missing:
        return
    new_header = existing + missing
    # ヘッダ行を更新
    ws.update([new_header], range_name="1:1", value_input_option="RAW")


# ============================================================
# 汎用 read / write (DataFrame 単位)
# ============================================================
# API節約のためのキャッシュ。
# 同じタブを短時間に繰り返し読む場合、実際のAPI呼び出しは1回で済む。
# 書き込み(write_sheet / append_row)時に該当タブのキャッシュを破棄して整合を保つ。
@st.cache_data(show_spinner=False, ttl=30)
def _read_sheet_cached(name: str) -> pd.DataFrame:
    """実際にスプレッドシートを読む処理(キャッシュ対象)。30秒キャッシュ。"""
    ws = _get_or_create_ws(name)
    records = ws.get_all_records()  # 1行目をヘッダとして dict のリスト
    if records:
        df = pd.DataFrame(records)
        for col in SHEET_SCHEMAS.get(name, []):
            if col not in df.columns:
                df[col] = ""
        return df
    header = ws.row_values(1) or SHEET_SCHEMAS.get(name, [])
    return pd.DataFrame(columns=header)


def _invalidate(name: str = None):
    """読み取りキャッシュを破棄する。name 指定時はそのタブだけ、無指定は全体。"""
    try:
        if name is None:
            _read_sheet_cached.clear()
        else:
            _read_sheet_cached.clear(name)
    except Exception:
        # clear(arg) 非対応版の保険として全体クリア
        try:
            _read_sheet_cached.clear()
        except Exception:
            pass


def read_sheet(name: str) -> pd.DataFrame:
    """タブ全体を DataFrame で返す(キャッシュ経由)。
    返した DataFrame を呼び出し側が変更してもキャッシュに影響しないようコピーを返す。"""
    return _read_sheet_cached(name).copy()


def write_sheet(name: str, df: pd.DataFrame):
    """DataFrame でタブ全体を上書きする(ヘッダ + 全行)。書き込み後キャッシュ破棄。"""
    ws = _get_or_create_ws(name)
    cols = list(df.columns)
    # NaN を空文字に。全セルを文字列化(gspread はネイティブ型も可だが安全側)
    safe = df.fillna("").astype(object)
    values = [cols] + safe.values.tolist()
    ws.clear()
    ws.update(values, value_input_option="RAW")
    _invalidate(name)


def append_row(name: str, row: dict):
    """1行を末尾に追記する。ヘッダの列順に並べ替えて入れる。書き込み後キャッシュ破棄。"""
    ws = _get_or_create_ws(name)
    header = ws.row_values(1)
    if not header:
        header = SHEET_SCHEMAS.get(name, list(row.keys()))
        ws.update([header], value_input_option="RAW")
    ordered = [_to_cell(row.get(col, "")) for col in header]
    ws.append_row(ordered, value_input_option="RAW")
    _invalidate(name)


def _to_cell(v):
    if v is None:
        return ""
    return v


# ============================================================
# スクショ: スプレッドシート内に縮小JPEG(Base64)で保存
# ------------------------------------------------------------
# サービスアカウントはマイドライブに保存容量を持たない(2023/6以降の仕様)ため、
# Drive ではなくスプレッドシートのセルに画像を格納する。
# セルは最大5万文字なので、画像を縮小JPEG化→Base64→45000字ごとに分割し、
# 専用タブ "screenshots" に1チャンク=1行で保存する。
#   列: shot_id(査定timestamp等で一意), idx(画像番号), chunk(分割番号), total_chunks, data
# ============================================================
_CHUNK = 45000          # 1セルあたりの最大文字数(5万字制限に余裕を持たせる)
_MAX_WIDTH = 720        # 縮小後の最大幅(px)
_JPEG_QUALITY = 72      # JPEG品質

# screenshots タブのスキーマを登録
SHEET_SCHEMAS["screenshots"] = ["shot_id", "idx", "chunk", "total_chunks", "data"]


def _resize_to_jpeg(file_bytes: bytes) -> bytes:
    """画像を最大幅 _MAX_WIDTH に縮小し、JPEG にして返す。
    Pillow が無い/壊れ画像の場合は元バイトをそのまま返す(保険)。"""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(file_bytes))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        if w > _MAX_WIDTH:
            im = im.resize((_MAX_WIDTH, int(h * _MAX_WIDTH / w)))
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=_JPEG_QUALITY)
        return out.getvalue()
    except Exception:
        return file_bytes


def save_screenshot(shot_id: str, idx: int, file_bytes: bytes) -> int:
    """1枚の画像を縮小・Base64化・分割して screenshots タブに保存する。
    返り値はチャンク数。shot_id は査定を一意に識別する文字列(timestamp等)。"""
    import base64
    jpeg = _resize_to_jpeg(file_bytes)
    b64 = base64.b64encode(jpeg).decode("ascii")
    chunks = [b64[i:i + _CHUNK] for i in range(0, len(b64), _CHUNK)] or [""]
    total = len(chunks)
    ws = _get_or_create_ws("screenshots")
    rows = [[shot_id, idx, c_i, total, chunk] for c_i, chunk in enumerate(chunks)]
    ws.append_rows(rows, value_input_option="RAW")
    _invalidate("screenshots")
    return total


def load_screenshots(shot_id: str) -> list:
    """指定 shot_id の画像をすべて復元し、JPEGバイトのリストで返す(idx順)。"""
    import base64
    df = read_sheet("screenshots")
    if df.empty or "shot_id" not in df.columns:
        return []
    sub = df[df["shot_id"].astype(str) == str(shot_id)]
    if sub.empty:
        return []
    images = []
    # idx ごとにまとめ、chunk順に連結
    for idx_val in sorted(sub["idx"].astype(int).unique()):
        g = sub[sub["idx"].astype(int) == idx_val].copy()
        g["chunk"] = g["chunk"].astype(int)
        g = g.sort_values("chunk")
        b64 = "".join(g["data"].astype(str).tolist())
        try:
            images.append(base64.b64decode(b64))
        except Exception:
            continue
    return images
