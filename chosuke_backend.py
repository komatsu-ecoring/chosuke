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
import re
import time
from datetime import datetime, timedelta

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


# ============================================================
# v0.17.0: screenshots の保存期間管理
# ------------------------------------------------------------
# 2026-09-16、旧スプレッドシートが 1000万セルの上限に達して
# 「永続的な読み取り専用モード」に切り替わり、試験中に書き込みが
# 一切できなくなった。原因は screenshots タブの無制限な積み上げ。
# 予兆が何も出なかったため、
#   (1) 一定期間より古い画像を自動で削除する
#   (2) 現在の使用量を画面で見えるようにする
# の2つを入れる。
# ============================================================
SCREENSHOT_RETENTION_DAYS = 90      # これより古い画像は自動削除
SCREENSHOT_KEEP_PREFIXES = ("LV1-", "LV2-", "LV3-")  # 試験の写真は制度の記録なので残す

_SHOT_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _shot_id_date(shot_id: str):
    """shot_id に埋まっている日付を取り出す。
    査定・トレーニングは timestamp そのもの、試験は
    'LV1-0916::Sokry::2026-09-16T02:36:25::q1' の形式。"""
    m = _SHOT_DATE_RE.search(str(shot_id))
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def screenshot_usage() -> dict:
    """screenshots タブの使用量を返す。設定モードの表示用。"""
    df = read_sheet("screenshots")
    rows = len(df)
    cols = len(SHEET_SCHEMAS["screenshots"])
    images = 0
    if not df.empty and "shot_id" in df.columns and "idx" in df.columns:
        images = len(df[["shot_id", "idx"]].astype(str).drop_duplicates())
    return {
        "rows": rows,
        "cells": rows * cols,
        "images": images,
        "limit": 10_000_000,
        "pct": (rows * cols) / 10_000_000 * 100,
    }


def purge_old_screenshots(days: int = None, dry_run: bool = False) -> dict:
    """保存期間を過ぎた画像を screenshots から削除する。

    - 日付を読み取れない shot_id は安全側に倒して残す
    - SCREENSHOT_KEEP_PREFIXES で始まる shot_id(試験の写真)は残す
    - 削除対象が無ければ書き込みを行わない(API節約)
    """
    days = SCREENSHOT_RETENTION_DAYS if days is None else days
    df = read_sheet("screenshots")
    if df.empty or "shot_id" not in df.columns:
        return {"deleted_rows": 0, "deleted_images": 0, "kept_rows": 0}

    cutoff = datetime.now() - timedelta(days=days)

    def _keep(sid) -> bool:
        s = str(sid)
        if s.startswith(SCREENSHOT_KEEP_PREFIXES):
            return True
        d = _shot_id_date(s)
        if d is None:
            return True
        return d >= cutoff

    mask = df["shot_id"].map(_keep)
    kept = df[mask]
    dropped = df[~mask]
    if dropped.empty:
        return {"deleted_rows": 0, "deleted_images": 0, "kept_rows": len(kept)}

    n_img = 0
    if "idx" in dropped.columns:
        n_img = len(dropped[["shot_id", "idx"]].astype(str).drop_duplicates())

    if not dry_run:
        write_sheet("screenshots", kept.reset_index(drop=True))

    return {
        "deleted_rows": int(len(dropped)),
        "deleted_images": int(n_img),
        "kept_rows": int(len(kept)),
    }


# ============================================================
# v0.17.1: 旧スプレッドシートからの画像復旧
# ------------------------------------------------------------
# 2026-09-16 の障害で Chosuke_Data → Chosuke_Data_v2 へ移行した際、
# screenshots タブの行が新ファイルへ渡りきらなかった。その結果、
# 移行前(9/15〜9/16午前)のトレーニング提出が、評価画面に
# 「画像なし」で出る状態になっている。
#
# 旧ファイルは読み取り専用だが「読む」ことはできるので、
# 必要な shot_id の行だけを拾って新ファイルへ戻す。
#
# 設計上の注意:
#   - 旧ファイルは 96MB ある。全部は読まない。
#   - data 列(1セル45000字)を含む読み取りは、必要な行だけに絞る。
#   - 索引づくりは A列 → 必要行の A:D、の2段階。ここは軽い。
#   - 戻すのは「参照されていて、新ファイルに無く、旧ファイルに揃っている」画像だけ。
# ============================================================
LEGACY_SPREADSHEET_ID = "18-dDpZefqJG2ynWXO5ZeJx7dcV7B787d1WRa-LUR-7k"

_RESTORE_MAX_CHARS = 2_000_000   # 1回の追記で送る最大文字数(APIペイロード上限の安全側)
_FETCH_ROWS_PER_RANGE = 40       # data列を含めて一度に取る最大行数


@st.cache_resource(show_spinner=False)
def _get_legacy_spreadsheet() -> gspread.Spreadsheet:
    """旧スプレッドシートを開く。Secrets に legacy_spreadsheet_id があればそれを使う。"""
    try:
        sid = st.secrets.get("legacy_spreadsheet_id", LEGACY_SPREADSHEET_ID)
    except Exception:
        sid = LEGACY_SPREADSHEET_ID
    return _get_gspread_client().open_by_key(sid)


def _to_int(v, default: int = -1) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default


def _contiguous_ranges(row_nos: list, max_rows: int) -> list:
    """連続する行番号を (開始, 終了) の範囲にまとめる。max_rows で頭打ちにする。"""
    out = []
    if not row_nos:
        return out
    start = prev = row_nos[0]
    for r in row_nos[1:]:
        if r == prev + 1 and (prev - start + 1) < max_rows:
            prev = r
            continue
        out.append((start, prev))
        start = prev = r
    out.append((start, prev))
    return out


def _shot_index_from_ws(ws) -> pd.DataFrame:
    """screenshots タブの A:D(重い data 列を除く)を読み、行番号付きの索引を返す。
    列: shot_id / idx / chunk / total_chunks / row_no(1始まり、ヘッダが1行目)"""
    try:
        vals = ws.get("A2:D")
    except Exception:
        vals = []
    recs = []
    for i, row in enumerate(vals or []):
        if not row or not str(row[0]).strip():
            continue
        recs.append({
            "shot_id": str(row[0]).strip(),
            "idx": _to_int(row[1]) if len(row) > 1 else -1,
            "chunk": _to_int(row[2]) if len(row) > 2 else -1,
            "total_chunks": _to_int(row[3]) if len(row) > 3 else -1,
            "row_no": i + 2,
        })
    return pd.DataFrame(recs, columns=["shot_id", "idx", "chunk", "total_chunks", "row_no"])


def _complete_images(idx_df: pd.DataFrame) -> set:
    """索引から「チャンクが揃っている画像」の (shot_id, idx) 集合を返す。
    障害中に途中までしか保存されなかった画像を弾くための判定。"""
    if idx_df is None or idx_df.empty:
        return set()
    out = set()
    for (sid, i), g in idx_df.groupby(["shot_id", "idx"]):
        total = int(g["total_chunks"].max())
        if total <= 0:
            continue
        chunks = set(int(c) for c in g["chunk"].tolist())
        if all(c in chunks for c in range(total)):
            out.add((str(sid), int(i)))
    return out


@st.cache_data(show_spinner=False, ttl=600)
def _legacy_shot_id_column() -> pd.DataFrame:
    """旧 screenshots の A列(shot_id)だけを読む。行番号付き。10分キャッシュ。"""
    ws = _get_legacy_spreadsheet().worksheet("screenshots")
    col = ws.col_values(1)
    recs = [{"shot_id": str(v).strip(), "row_no": i + 1}
            for i, v in enumerate(col) if i >= 1 and str(v).strip()]
    return pd.DataFrame(recs, columns=["shot_id", "row_no"])


def _legacy_index_for(shot_ids) -> pd.DataFrame:
    """旧ファイルから、指定 shot_id の行だけ A:D を読んで索引にする。"""
    want = {str(s) for s in shot_ids if str(s).strip()}
    empty = pd.DataFrame(columns=["shot_id", "idx", "chunk", "total_chunks", "row_no"])
    if not want:
        return empty
    colf = _legacy_shot_id_column()
    if colf.empty:
        return empty
    hit = colf[colf["shot_id"].isin(want)]
    if hit.empty:
        return empty

    ws = _get_legacy_spreadsheet().worksheet("screenshots")
    ranges = _contiguous_ranges(sorted(int(r) for r in hit["row_no"].tolist()), max_rows=2000)
    recs = []
    for i in range(0, len(ranges), 20):
        part = ranges[i:i + 20]
        got = ws.batch_get([f"A{a}:D{b}" for a, b in part])
        for (a, _b), block in zip(part, got):
            for j, row in enumerate(block or []):
                if not row or not str(row[0]).strip():
                    continue
                recs.append({
                    "shot_id": str(row[0]).strip(),
                    "idx": _to_int(row[1]) if len(row) > 1 else -1,
                    "chunk": _to_int(row[2]) if len(row) > 2 else -1,
                    "total_chunks": _to_int(row[3]) if len(row) > 3 else -1,
                    "row_no": a + j,
                })
    return pd.DataFrame(recs, columns=["shot_id", "idx", "chunk", "total_chunks", "row_no"])


def _split_shot_ids(raw) -> list:
    """screenshot_ids 列("ts::market|ts::item" 形式)を分解する。"""
    s = str(raw or "").strip()
    if not s:
        return []
    return [p.strip() for p in s.split("|") if p.strip()]


def _shot_kind(shot_id: str) -> str:
    s = str(shot_id)
    if s.endswith("::market"):
        return "相場参考"
    if s.endswith("::item"):
        return "商品画像"
    if s.endswith("::expert"):
        return "相場データ(評価者)"
    return "画像"


def referenced_shot_ids(since: str = "", until: str = "") -> pd.DataFrame:
    """training_history / appraisal_history が参照している shot_id を一覧にする。
    since / until は 'YYYY-MM-DD'。timestamp の日付部分で絞る。"""
    rows = []

    th = read_sheet("training_history")
    if not th.empty:
        for _, r in th.iterrows():
            ts = str(r.get("timestamp", "") or "")
            d = ts[:10]
            if since and d < since:
                continue
            if until and d > until:
                continue
            label = f"{r.get('brand_ja', '')} {r.get('product_name', '')}".strip()
            for sid in _split_shot_ids(r.get("screenshot_ids", "")):
                rows.append({"source": "トレーニング", "timestamp": ts,
                             "staff": str(r.get("staff", "") or ""), "item": label,
                             "kind": _shot_kind(sid), "shot_id": sid,
                             "review_status": str(r.get("review_status", "") or "")})
            exp = str(r.get("expert_screenshot_ids", "") or "").strip()
            if exp:
                rows.append({"source": "トレーニング", "timestamp": ts,
                             "staff": str(r.get("staff", "") or ""), "item": label,
                             "kind": _shot_kind(exp), "shot_id": exp,
                             "review_status": str(r.get("review_status", "") or "")})

    ah = read_sheet("appraisal_history")
    if not ah.empty:
        for _, r in ah.iterrows():
            ts = str(r.get("timestamp", "") or "")
            d = ts[:10]
            if since and d < since:
                continue
            if until and d > until:
                continue
            label = f"{r.get('brand_ja', '')} {r.get('product_name', '')}".strip()
            for sid in _split_shot_ids(r.get("screenshot_ids", "")):
                rows.append({"source": "査定", "timestamp": ts,
                             "staff": str(r.get("staff", "") or ""), "item": label,
                             "kind": _shot_kind(sid), "shot_id": sid,
                             "review_status": str(r.get("review_status", "") or "")})

    return pd.DataFrame(rows, columns=["source", "timestamp", "staff", "item",
                                       "kind", "shot_id", "review_status"])


def diagnose_screenshots(since: str = "", until: str = "") -> dict:
    """指定期間の提出について、画像が新ファイルに在るか／旧ファイルから戻せるかを判定する。
    書き込みは一切しない。"""
    ref = referenced_shot_ids(since, until)
    if ref.empty:
        return {"table": ref, "restorable": [], "counts": {},
                "note": "この期間に画像を参照している提出がありませんでした。"}

    cur_idx = _shot_index_from_ws(_get_or_create_ws("screenshots"))
    cur_ok = _complete_images(cur_idx)
    cur_ok_ids = {sid for sid, _ in cur_ok}
    cur_any_ids = set(cur_idx["shot_id"].tolist()) if not cur_idx.empty else set()

    wanted = sorted(set(ref["shot_id"].tolist()))
    legacy_err = ""
    try:
        legacy_idx = _legacy_index_for(wanted)
    except Exception as e:
        legacy_idx = pd.DataFrame(columns=["shot_id", "idx", "chunk", "total_chunks", "row_no"])
        legacy_err = str(e)
    legacy_ok = _complete_images(legacy_idx)
    legacy_ok_ids = {sid for sid, _ in legacy_ok}
    legacy_any_ids = set(legacy_idx["shot_id"].tolist()) if not legacy_idx.empty else set()

    def _status(sid: str) -> str:
        if sid in cur_ok_ids:
            return "✅ 表示できる"
        if sid in legacy_ok_ids:
            return "🟡 旧から戻せる"
        if sid in legacy_any_ids:
            return "⚠️ 旧にもチャンク欠け"
        if sid in cur_any_ids:
            return "⚠️ 新にチャンク欠け"
        return "❌ どちらにも無い"

    def _n_images(sid: str) -> int:
        return len([1 for s, _ in (cur_ok | legacy_ok) if s == sid])

    table = ref.copy()
    table["状態"] = table["shot_id"].map(_status)
    table["枚数"] = table["shot_id"].map(_n_images)

    restorable = sorted({sid for sid in wanted
                         if sid not in cur_ok_ids and sid in legacy_ok_ids})
    counts = {
        "参照されている画像群": len(wanted),
        "表示できる": len([s for s in wanted if s in cur_ok_ids]),
        "旧から戻せる": len(restorable),
        "戻せない": len([s for s in wanted
                       if s not in cur_ok_ids and s not in legacy_ok_ids]),
        "戻す行数": int(len(legacy_idx[legacy_idx["shot_id"].isin(restorable)]))
        if not legacy_idx.empty else 0,
    }
    return {"table": table, "restorable": restorable, "counts": counts,
            "note": "", "legacy_error": legacy_err}


def restore_screenshots_from_legacy(shot_ids: list, dry_run: bool = False) -> dict:
    """旧ファイルから指定 shot_id の行を読み、新ファイルの screenshots へ追記する。
    - 新ファイルに既に揃っている (shot_id, idx) は書かない(二重登録の防止)
    - 旧ファイル側でチャンクが欠けている画像は書かない
    """
    want = {str(s) for s in shot_ids if str(s).strip()}
    result = {"restored_images": 0, "restored_rows": 0, "skipped_images": 0, "error": ""}
    if not want:
        return result

    try:
        legacy_idx = _legacy_index_for(want)
    except Exception as e:
        result["error"] = f"旧ファイルを読めませんでした: {e}"
        return result
    if legacy_idx.empty:
        result["error"] = "旧ファイルに該当する行がありませんでした。"
        return result

    legacy_ok = _complete_images(legacy_idx)
    cur_ws = _get_or_create_ws("screenshots")
    cur_ok = _complete_images(_shot_index_from_ws(cur_ws))

    keep_keys = {k for k in legacy_ok if k not in cur_ok}
    result["skipped_images"] = len(legacy_ok) - len(keep_keys)
    if not keep_keys:
        return result

    mask = legacy_idx.apply(
        lambda r: (str(r["shot_id"]), int(r["idx"])) in keep_keys, axis=1)
    target = legacy_idx[mask]
    if target.empty:
        return result

    result["restored_images"] = len(keep_keys)
    if dry_run:
        result["restored_rows"] = int(len(target))
        return result

    ws = _get_legacy_spreadsheet().worksheet("screenshots")
    row_nos = sorted(int(r) for r in target["row_no"].tolist())
    ranges = _contiguous_ranges(row_nos, max_rows=_FETCH_ROWS_PER_RANGE)

    batch, size, written = [], 0, 0
    for a, b in ranges:
        block = ws.batch_get([f"A{a}:E{b}"])
        rows = block[0] if block else []
        for row in rows or []:
            if not row or not str(row[0]).strip():
                continue
            key = (str(row[0]).strip(), _to_int(row[1]) if len(row) > 1 else -1)
            if key not in keep_keys:
                continue
            cell = [str(row[0]).strip(),
                    row[1] if len(row) > 1 else "",
                    row[2] if len(row) > 2 else "",
                    row[3] if len(row) > 3 else "",
                    row[4] if len(row) > 4 else ""]
            rl = len(str(cell[4]))
            if batch and size + rl > _RESTORE_MAX_CHARS:
                cur_ws.append_rows(batch, value_input_option="RAW")
                written += len(batch)
                batch, size = [], 0
            batch.append(cell)
            size += rl
    if batch:
        cur_ws.append_rows(batch, value_input_option="RAW")
        written += len(batch)

    result["restored_rows"] = written
    _invalidate("screenshots")
    return result
