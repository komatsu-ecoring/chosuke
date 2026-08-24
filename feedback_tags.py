"""
Chosuke — フィードバック・タグ機能 (v0.16)
==========================================
目的:
  レビューのフィードバックを「自由記述1本」から「タグ + 一行テキスト × 最大5」に構造化し、
  (1) staff ごとの弱点をタグ集計で可視化する
  (2) 同じ指摘の再発回数をレビュアーと staff の両方に見せる
  ことを可能にする。

設計判断:
  - 縦持ち: training_history に fb1_tag..fb5_text と 10 列足すのではなく、
    feedback_items タブに 1 項目 = 1 行で持つ。集計が groupby 一発で済み、
    項目数の上限を将来変えても列追加が要らない。
  - タグは固定7 + 自由入力。自由入力は「まだ名前の付いていない指摘」を拾うセンサー。
    月1回見直し、頻出したものを固定タグへ昇格させる運用を想定。
  - 表示名は用語集(2026-08 確定)に準拠。staff 向け表記は英語で統一。

依存: chosuke_backend (be) の read_sheet / write_sheet / append_row のみ。
"""

from __future__ import annotations

import pandas as pd
from datetime import datetime

import chosuke_backend as be


SHEET = "feedback_items"

COLUMNS = [
    "item_id",        # 一意キー: "<record_ts>::<seq>"
    "record_ts",      # 対象提出の timestamp (training_history と結合するキー)
    "source",         # "training" | "appraisal"
    "test_id",        # 定期試験の識別子(通常トレーニングは空)。将来の③で使用
    "staff",          # 指摘を受けた staff
    "reviewer",       # 指摘した人
    "reviewed_at",    # 評価日時
    "seq",            # 1..5
    "tag",            # 固定タグの内部キー、または自由入力文字列
    "text_ja",        # 指摘本文(日本語・原文)
    "text_en",        # 指摘本文(英語)。当面は空。翻訳導入時に埋める
]

# --- 固定タグ (用語集 ③タグ シート準拠) -------------------------------------
# key: 内部キー(不変)。ja/en: 表示名。step: 手順書の対応STEP。
TAGS = [
    {"key": "item_id_check", "ja": "商品特定",     "en": "Item identification",      "step": "STEP 1"},
    {"key": "rank",          "ja": "Rank判定",     "en": "Rank assessment",          "step": "STEP 2"},
    {"key": "condition",     "ja": "状態・付属品", "en": "Condition & accessories",  "step": "STEP 2"},
    {"key": "market_method", "ja": "相場の調べ方", "en": "Market research method",   "step": "STEP 3"},
    {"key": "price",         "ja": "価格判断",     "en": "Price judgement",          "step": "STEP 4"},
    {"key": "input_error",   "ja": "入力ミス",     "en": "Input error",              "step": "—"},
    {"key": "item_choice",   "ja": "題材選択",     "en": "Choice of practice item",  "step": "—"},
]

TAG_KEYS = [x["key"] for x in TAGS]
_TAG_BY_KEY = {x["key"]: x for x in TAGS}

FREE_TAG_PREFIX = "free:"   # 自由入力タグは "free:<文字列>" として保存する


def tag_label(tag: str, lang: str = "ja") -> str:
    """内部キー or 自由入力タグ を表示名に変換する。未知の値はそのまま返す。"""
    tag = str(tag or "").strip()
    if not tag:
        return ""
    if tag.startswith(FREE_TAG_PREFIX):
        return tag[len(FREE_TAG_PREFIX):]
    rec = _TAG_BY_KEY.get(tag)
    if not rec:
        return tag
    return rec.get(lang) or rec["ja"]


def tag_options(lang: str = "ja") -> list:
    """selectbox 用の (表示名, キー) ペア。先頭に空選択を置く。"""
    return [("—", "")] + [(tag_label(k, lang), k) for k in TAG_KEYS]


# --- シート I/O ---------------------------------------------------------------
def ensure_sheet() -> None:
    """feedback_items タブが無ければヘッダだけ作る。
    chosuke_backend の init_backend スキーマに手を入れずに済ませるため、
    read に失敗した場合のみ空フレームを書き込む(既存データは絶対に触らない)。"""
    try:
        df = be.read_sheet(SHEET)
    except Exception:
        df = None
    if df is None or (isinstance(df, pd.DataFrame) and df.empty and list(df.columns) != COLUMNS):
        try:
            be.write_sheet(SHEET, pd.DataFrame(columns=COLUMNS))
        except Exception:
            pass


def load_items() -> pd.DataFrame:
    """全フィードバック項目。取得できない場合は空フレームを返す(画面は落とさない)。"""
    try:
        df = be.read_sheet(SHEET)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNS)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df


def save_items(record_ts: str, staff: str, reviewer: str, reviewed_at: str,
               items: list, source: str = "training", test_id: str = "") -> int:
    """1件の提出に紐づくフィードバック項目をまとめて追記する。

    items: [{"tag": <キー or free:...>, "text": "..."}] の順序付きリスト。
           tag も text も空の要素は保存しない(=①〜⑤は任意で、埋めなくてよい)。
    戻り値: 実際に保存した件数。
    既に同じ record_ts の項目があれば削除してから書き直す(再評価に対応)。
    """
    rows = []
    seq = 0
    for it in items:
        tag = str(it.get("tag", "") or "").strip()
        text = str(it.get("text", "") or "").strip()
        if not tag and not text:
            continue
        seq += 1
        rows.append({
            "item_id": f"{record_ts}::{seq}",
            "record_ts": record_ts,
            "source": source,
            "test_id": test_id,
            "staff": staff,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "seq": seq,
            "tag": tag,
            "text_ja": text,
            "text_en": "",
        })

    df = load_items()
    if not df.empty:
        df = df[df["record_ts"].astype(str) != str(record_ts)]
    new = pd.DataFrame(rows, columns=COLUMNS) if rows else pd.DataFrame(columns=COLUMNS)
    out = pd.concat([df, new], ignore_index=True) if not df.empty else new
    try:
        be.write_sheet(SHEET, out[COLUMNS])
    except Exception:
        return 0
    return len(rows)


# --- 集計 ---------------------------------------------------------------------
def tag_counts(staff: str = "", last_n_records: int = 0) -> pd.DataFrame:
    """staff のタグ別件数。多い順。

    last_n_records > 0 のとき、直近その件数の「提出」に絞る(項目数ではない)。
    戻り値: columns=[tag, label_ja, label_en, count]
    """
    df = load_items()
    if df.empty:
        return pd.DataFrame(columns=["tag", "label_ja", "label_en", "count"])
    if staff:
        df = df[df["staff"].astype(str).str.strip() == str(staff).strip()]
    if df.empty:
        return pd.DataFrame(columns=["tag", "label_ja", "label_en", "count"])
    if last_n_records and last_n_records > 0:
        recent = (df[["record_ts"]].drop_duplicates()
                    .sort_values("record_ts", ascending=False)
                    .head(last_n_records)["record_ts"].tolist())
        df = df[df["record_ts"].isin(recent)]

    g = (df[df["tag"].astype(str).str.strip() != ""]
         .groupby("tag").size().reset_index(name="count")
         .sort_values("count", ascending=False))
    g["label_ja"] = g["tag"].map(lambda x: tag_label(x, "ja"))
    g["label_en"] = g["tag"].map(lambda x: tag_label(x, "en"))
    return g[["tag", "label_ja", "label_en", "count"]].reset_index(drop=True)


RECUR_WINDOW = 10   # 再発判定の窓（提出件数）
RECUR_LIMIT  = 3    # この回数以上で未解消


def recurrence(staff: str, tag: str, last_n_records: int = 0) -> int:
    """この staff がこのタグで指摘された回数。

    last_n_records > 0 のとき、直近その件数の「提出」に絞る。
    0（既定）のときは従来どおり累計を返す。
    """
    df = load_items()
    if df.empty or not staff or not tag:
        return 0
    df = df[df["staff"].astype(str).str.strip() == str(staff).strip()]
    if df.empty:
        return 0
    if last_n_records and last_n_records > 0:
        recent = (df[["record_ts"]].drop_duplicates()
                    .sort_values("record_ts", ascending=False)
                    .head(last_n_records)["record_ts"].tolist())
        df = df[df["record_ts"].isin(recent)]
    return int((df["tag"].astype(str).str.strip() == str(tag).strip()).sum())


def items_for_record(record_ts: str) -> pd.DataFrame:
    """特定の提出に紐づく項目を seq 順で返す(My Results / 再評価時の初期値に使う)。"""
    df = load_items()
    if df.empty:
        return df
    out = df[df["record_ts"].astype(str) == str(record_ts)].copy()
    if out.empty:
        return out
    out["_s"] = pd.to_numeric(out["seq"], errors="coerce").fillna(0)
    return out.sort_values("_s").drop(columns=["_s"])


# --- 乖離率 -------------------------------------------------------------------
def gap_rate(staff_offer, expert_min, expert_max):
    """乖離率(%) = price_gap / 正解レンジ中央値 * 100。

    price_gap は絶対額(USD)なので、商品の価格帯が違う staff 同士では比較できない。
    率に直すことで、各自が自由に題材を選んでも比較可能になる。
    レンジ内なら 0.0、算出不能なら None。
    """
    try:
        offer = float(staff_offer or 0)
        lo = float(expert_min or 0)
        hi = float(expert_max or 0)
    except (ValueError, TypeError):
        return None
    if offer <= 0 or lo <= 0 or hi <= 0:
        return None
    lo, hi = min(lo, hi), max(lo, hi)
    mid = (lo + hi) / 2.0
    if mid <= 0:
        return None
    if offer < lo:
        gap = offer - lo
    elif offer > hi:
        gap = offer - hi
    else:
        gap = 0.0
    return round(gap / mid * 100.0, 1)


# 合格ライン: 2026-08 の実績分布(12件)から決定。
#   絶対乖離率は 0,0,0,0,5.9,7.2,9.1,14.3,15.4,37.7,40.0,87.3 と分布し、
#   15.4% と 37.7% の間が空いている。粗利率で見ると +10% で約31%、+20% で約25%。
BAND_IN_RANGE = 0.0     # レンジ内
BAND_PASS = 10.0        # 合格(粗利率 約31% を維持できる圏)
BAND_WARN = 20.0        # 警戒(粗利率 約25%、会社が持つ下限)


def gap_band(rate) -> str:
    """乖離率をバンドに変換。'in_range' / 'pass' / 'warn' / 'fail' / '' """
    if rate is None:
        return ""
    a = abs(float(rate))
    if a <= BAND_IN_RANGE:
        return "in_range"
    if a <= BAND_PASS:
        return "pass"
    if a <= BAND_WARN:
        return "warn"
    return "fail"
