"""
Chosuke v0.10.9 — Eco Ring Cambodia AI Appraisal Assistant
========================================================
査定モード + 査定レビューモード + ナレッジ管理モード + 設定の4画面構成
ローカルCSVファイルベース(Googleドライブ同期想定)
APIなしでも動作。後でClaude API接続できるように拡張ポイントを用意。

============================================================
Chosuke 人格定義 (設計インサイト #004)
============================================================
Chosukeは「いかりや長介」的な口うるさい指導役。
- 答えを出さず、観察を促す合いの手を返す
- 「!」を多用し、くどくど確認させる
- 断定を避け「例外もある」と添える
- 鑑定士の手を止めさせ、ライト使用など具体動作を促す
- スタッフの「目」を育てる教育型システム

トーン原則:
× 「鍵紛失で大幅減額」(断定・答えを出している)
○ 「鍵単体の相場もあるので確認してみて」(観察を促す)

× 「相場は$2000です」(数字で答えを出す)
○ 「近年モデルですね!状態次第で強気に行けそう」(合いの手)

このトーンは v0.9 以降の全機能追加で一貫させること。
日本語のニュアンスに依存するため、クメール語版では別表現を要設計。

============================================================
言語切り替えについて
============================================================
v0.9では言語別メッセージ辞書 (MESSAGES) の構造を導入。
現在は日本語(ja)のみ運用、クメール語(km)は将来追加予定。
サイドバーで切り替え可能だが、kmは未翻訳のためjaにフォールバック。

v0.9の変更点(v0.8から):
- 年式タグ反応を実装(全年式に「いかりや長介トーン」のセリフ):
  * 直近2年以内 → 「近年モデルですね!状態次第で強気に行けそう」
  * 3〜5年 → 「準新作の範囲です。状態確認はしっかりね」
  * 6〜10年 → 「中堅年式。相場の動きを確認しましょう」
  * 10年超え → 「年代物ですね。原価率は50%あたりで交渉努力しましょう!
              ただし例外品もあるから気を付けて!キレイに見えても
              見にくいダメージ(カビ・内部加水分解)もあるから、
              コンディション確認をしっかりね!ライト使ってね!」
- 定番モデル反応を実装:
  * ブランドマスタに iconic_models 列を追加
  * 品名に該当キーワードが含まれていたら「定番モデルですね!需要安定型」
  * 主要ブランド(DIOR/CHANEL/HERMES/LV等)の定番を初期登録
- 人格定義をヘッダーコメントに明文化(設計インサイト #004)
- 言語切り替え構造の準備(MESSAGES辞書、現状ja固定)

v0.10.8の変更点(v0.10.7から):
- クリア/リセットがブラウザで効かない問題を修正(現場フィードバックより・最優先):
  * 【背景】v0.10.7のon_click直接pop方式は、自動テスト(AppTest)では確実に
    クリアできるのに、実ブラウザでは立ち上げ直後でも入力が残る現象が再現した。
    レイアウトコンテナ(st.columns)内ボタンのコールバック発火タイミング差が原因と推定。
  * 【修正】「クリアフラグ方式」に作り替え。on_click では _clear_requested フラグを
    立てるだけ(_request_appraisal_clear)。実際の pop は appraisal_mode() の冒頭
    =全ウィジェット生成より前で _apply_appraisal_clear_if_requested() が行う。
    コールバック発火タイミングに依存せず、再描画の最初に必ずクリアが走る。
    上部クリア・下部リセット両方をこの方式に統一。担当staffは引き続き残す。

v0.10.7の変更点(v0.10.6から):
- クリア/リセットが効かないバグを修正(現場フィードバックより・最優先):
  * 【背景】v0.10.6で入れたクリア機能が効かず、ブランド・品名・Rank・付属品・
    チェック類・相場メモ・スクショが残ったまま(応答だけ初期化)になっていた。
  * 【原因】「if st.button(): _clear(); st.rerun()」方式だと、ボタンより後ろに
    定義されたウィジェットが再描画時に値を session_state へ書き戻すため、
    pop しても消えたように見えない(Streamlit既知の挙動。公式Docs/Issue#5442参照)。
  * 【修正】上部クリア・下部リセットを on_click コールバック方式に変更。
    on_click はウィジェット描画前に実行されるため、pop が確実に効く。
    file_uploader(スクショ)含め全入力が消えることを実機で確認済み。
- フォールバック時の案内文を削除(現場フィードバック: 不要・くどい):
  * v0.10.6で入れた「『○○』で登録済みのブランドはまだ無いから〜」を削除。
    フォールバック挙動(ブランドが消えない)はそのまま維持。黙って全表示にする。

v0.10.6の変更点(v0.10.5から):
- カテゴリ絞り込みフィルタの取りこぼしを修正(現場フィードバックより):
  * 【背景】ブランド選択済みでカテゴリ(スカーフ/アクセサリー/SLG/ベルト等)を選ぶと、
    そのカテゴリに紐づく登録ブランドが0件になり、選んでいたブランドが候補から消えた。
    実害として、ヴィトンのスカーフを「その他/未登録」で手入力するしかなくなり、
    ブランド固有ロジック(年式判定・notes・原価率基準値)が全て無効化されていた。
    原因は BRAND_CATEGORY_NORMALIZE がスカーフ/アクセサリー等への正規化先を持たず、
    かつ実マスタの category が1ブランド1値(バッグ/時計/ジュエリー/服/靴/他の)しか
    持てない構造のため、それ以外のカテゴリは必ず完全一致せず0件になっていた。
  * 【修正】絞り込み結果が0件なら自動で全ブランド表示に戻すフォールバックを追加。
    ブランドを消さないことを最優先化(取りこぼし根絶)。警告文も、観察を促す穏やかな
    案内に変更(原価率は選んだカテゴリ補正で計算される旨を明示)。
    ※ category 複数値対応(根本解決)は将来課題としてメモ。
- リセット挙動を再定義(現場フィードバックより):
  * 【背景】従来のリセットは advice_result/advice_meta(=Chosuke応答)だけクリアし、
    商品情報も担当者も残ったままだった。
  * 【修正】_clear_appraisal_inputs() を新設。担当staffは残し、商品情報・相場メモ・
    付属品/細部確認チェック・スクショ・応答をクリアする挙動に統一。
    同じ担当者が次々に違う商品を査定する現場フローに合わせた。
- 上部クリアボタンを追加(現場フィードバックより):
  * 査定モード見出しの右端に「🔄 クリア」を併設。下までスクロールせず上部でリセット可能。
    動作は下部リセットと同一(_clear_appraisal_inputs を共用)。

v0.10.5の変更点(v0.10.4から):
- 年式を「上限(天井)」にも効かせる(year_upper_correction 新設):
  * 【背景】従来、年式は下限の幅にしか効かず、新品でも年代物でも上限が同じだった。
    年代物エルメスでも天井が73%のままで「原価率が高い」状態だった。
  * 【修正】cost_params.json に year_upper_correction を追加(全ブランド共通)。
    上限計算式に組み込み: 上限 = ... + 定番 + 年式上限補正。
    補正値: 近年0 / 準新作-2 / 中堅-4 / 年代物-7。
    -> 年代物エルメスが 65〜73% から 58〜66% に。古いほど天井から下がる。
  * 思考過程カードの独り言に「天井そのものを-7%抑える」を追加。
  * 年式幅(下限)は v0.5.1 のまま(近年3/準新作6/中堅7/年代物8)。
    上限補正(天井を下げる)と年式幅(下限の開き)は別の効き方をする2軸。

v0.10.4の変更点(v0.10.3から):
- 付属品の欠品に対するChosukeのコメントを追加(設計インサイト #002):
  * 【背景】「一部欠品」で品目をチェックしても、その内容が応答ロジックに
    渡っておらず、Chosukeが欠品に一切触れていなかった(履歴CSVに残るだけ)。
    ピコタンの鍵欠品など、観察を促すべき場面でChosukeが沈黙していた。
  * 【修正】missing_items を chosuke_advise() に渡し、品目別の観察促しを生成。
    build_missing_items_advice() を新設。UIに「欠品アドバイスカード」を追加。
  * トーン原則を厳守: 「鍵紛失で大幅減額」(断定)ではなく
    「鍵・カデナは単体でも相場がある、即減額と決めつけるな、確認しろ」(観察促し)。
    鍵・カデナ・ストラップは単体相場に触れて厚めに、箱・保存袋・取説は軽めに。
  * 欠品が無ければカードは出ない。tip未定義の品目・自由記述もまとめて拾う。
- ※推奨原価率の「幅が広い」問題(年式幅 年代物-12)は別途検討中。
  幅は cost_params.json の year_range_width_below_upper の数値で決まる(コード変更不要)。

v0.10.3の変更点(v0.10.2から):
- 査定モードの入力欄レイアウトを改善(付属品チェックリストの視認性):
  * 【背景】付属品で「一部欠品」を選んだとき、詳細チェックリストが
    ギャランティーカード・製造年フラグの2セクション下に離れて表示され、
    視線が途切れてチェックを飛ばされやすかった。
  * 【修正】3カラム(製造年/付属品/Rank)から付属品を外して単独行にし、
    その直下に「一部欠品」の詳細チェックリストを配置。
    選択→入力の視線が途切れないようにした。製造年/Rankは2カラムで維持。
  * ギャランティーカード・製造年フラグはチェックリストの後ろに移動(欠品と無関係なため)。

v0.10.2の変更点(v0.10.1から):
- 年式の「効き方」を表示で分かるように整合(計算ロジックは変更なし):
  * 【背景】年式は上限ではなく「上限から下げて下限を取る幅」に効く設計だが、
    思考過程カードの独り言に年式が登場せず「年式が反映されてない」ように見えた。
    さらに年式タグの「原価率は50%あたりで交渉努力」という断定数字が、
    レンジ表示(例:61〜73%)と食い違って見えていた。
  * 【修正1】build_cost_thinking_text() に年式幅の独り言を追加。
    「年代物だから下振れ幅を広めに取る…上限から−12%」と思考過程に明示。
  * 【修正2】year_old メッセージから断定数字「50%あたり」を削除。
    「強気の天井より下振れリスクを見ろ/下限側を厚めに」のトーンに変更し、
    レンジ表示と矛盾しないようにした。
- 敬語の混入を修正(Chosukeのセリフ部分のみいかりや調へ統一):
  * market_range_check() の4メッセージ(相場の幅判定)
  * 過去履歴比較メッセージ
  * ※管理画面のUI説明文・ボタンヘルプは操作説明なので敬語のまま据え置き

v0.10.1の変更点(v0.10から):
- 促し動作(ルーペ/ライト等の確認動作)を独立カード化:
  * 【背景】v0.10では促し動作が思考過程カードの末尾にしか無く、
    思考過程カードは「動的算出(Layer2)」のときだけ表示されていた。
    そのため実績3件以上(Layer3)やJSON無し(Layer1)では促し動作が消えていた。
    → 売れ筋ほど実績が貯まりLayer3に昇格し、皮肉にも促し動作が出なくなる問題。
  * 【修正】促し動作のカテゴリ判定を Layer 判定の外に出し、
    chosuke_advise() 戻り値に inspection_tip / inspect_cat を常時格納。
    UI に独立した「確認動作カード」を追加し、Layerに関係なく毎回表示。
  * カテゴリ判定優先順位: 電子機器(専用) > 査定カテゴリ(絞り込み) > マスタcategory正規化 > 空(デフォルト文)
  * build_cost_thinking_text() の末尾からは促し動作を除去(二重表示防止)。
    inspect_cat 引数は後方互換のため残置(本文未使用)。
  * 電子機器(アップル等)は専用の確認動作文を追加:
    アクティベーションロック解除確認 / 型番・容量(GB)・カラー照合 / 起動・バッテリー確認。
    マスタcategory="電子機器" を最優先で拾うため、文房具等その他の「他の」とは混ざらない。
    将来サムスン・ソニー等を電子機器として登録すれば自動で同じ促し文が出る。

v0.10の変更点(v0.9から):
- 推奨原価率の動的算出を実装(設計インサイト #003 / #005 / #006):
  * 計算式(案③ハイブリッド・上限ベース):
    上限 = ブランド基準値 + カテゴリ補正 + Rank補正 + ギャラ補正 + 付属品補正 + (定番なら+2)
    下限 = 上限 − 年式幅
    推奨レンジ = 下限 〜 上限
  * パラメータは外部JSON (Chosuke_Data/cost_params.json) から読み込み(方式B)
    → 別ツール cost_ratio_simulator で調整し、JSONを差し替えるだけで反映
  * Layer構造: 実績3件以上(Layer3) > 動的算出(Layer2/新規) > マスタ素値(Layer1)
  * cost_params.json が無い場合はマスタ素値にフォールバック(後方互換)
- 思考過程カードを追加(設計インサイト #004):
  * 「え〜と、◯◯だろぉ?基準は◯%から…Rankで+◯%…」と計算過程を独り言で展開
  * 前半=思考の言語化(教育)、後半=いかりや調で観察を促す(指導)
  * 数字だけでなく「どう組み立てたか」を見せ、鑑定士の思考を育てる
- 査定モードにギャランティーカード有無の入力欄を追加(有り/無し/対象外)
- ブランド選択を初期空欄化(index=None、検索しやすく) ※v0.9.1相当
- 推奨レンジは「○〜○%」のレンジ表示(上限=攻めていい天井、の発想)

v0.8の変更点(v0.7から):
- 商品情報入力欄の並び順を変更:
  担当staff(最上部・必須化) → ブランド → カテゴリ → 品名 → ...
  * 担当staffを最上部に移動し、未入力時は「Chosukeに相談する」ボタンを無効化
  * 履歴で「誰が査定したか」を確実に追跡できるようにする
  * カテゴリとブランドの順を入れ替え。ブランドが主、カテゴリは絞り込み補助。
- hint文の表現原則を「教育型」に統一する第一歩:
  * 「鍵紛失で大幅減額」→「鍵単体の相場もあるので確認してみて」
  * 断定的な減額表現を、観察を促すトーンに置き換え
  * 設計インサイト#002: Chosukeはスタッフの「目」を育てる教育型システム

v0.7の変更点(v0.6から):
- 商品情報入力欄に「カテゴリ」フィールドを新設(ブランドと品名の間)
  * 14カテゴリのプルダウン
  * 「指定なし」を選ぶと全ブランド表示、カテゴリを選ぶと絞り込み
- 製造年欄に「マイクロチップ品(2021年以降)」「年式不明」チェックボックス追加
- CHANEL シリアル年式判定テーブルを全面修正(社内資料準拠)
- CHANEL バッグの細部確認チェックリストに5項目追加
- 全カテゴリ共通で「相場根拠は充分か?」を細部確認の先頭に固定表示
"""

import streamlit as st
import pandas as pd
import os
import re
import json
from datetime import datetime
from pathlib import Path

import chosuke_backend as be

# ============================================================
# 設定: データ保存先
# ============================================================
DEFAULT_DATA_DIR = Path.home() / "Chosuke_Data"

# 事前登録する staff 名簿(staff_master タブが空のとき自動投入する初期値)
DEFAULT_STAFF_ROSTER = ["Soknan", "Bunlong", "Sreynich", "Dany", "Xing", "Pichi", "Komatsu"]

# ============================================================
# Rank選択肢(Eco Ring体系)
# ============================================================
RANK_OPTIONS = ["未定", "N", "S", "A", "AB", "B+", "B", "B-", "BC", "C", "D"]


def _rank_display(value: str) -> str:
    """Rank選択肢の表示。記号(N/S/A/B…)はそのまま、「未定」だけ英語を併記する。
    内部値・履歴保存・照合(rank != '未定' 等)はすべて日本語値のまま。"""
    if value == "未定":
        return "未定 / TBD"
    return value

# ============================================================
# カテゴリ選択肢(Eco Ring社内システム準拠)
# ============================================================
CATEGORY_OPTIONS = [
    "指定なし",
    "SLG",
    "アクセサリー",
    "ジュエリー",
    "スカーフ",
    "バッグ",
    "ファッションジュエリー",
    "ベルト",
    "メガネ・サングラス",
    "他の",
    "化粧品",
    "時計",
    "服",
    "靴",
    "高級ジュエリー",
]

# カテゴリの英訳(履歴・分析用)
CATEGORY_EN_MAP = {
    "SLG": "SLG",
    "アクセサリー": "ACCESSORY",
    "ジュエリー": "JEWELRY",
    "スカーフ": "SCARF",
    "バッグ": "BAG",
    "ファッションジュエリー": "FASHION JEWELRY",
    "ベルト": "BELT",
    "メガネ・サングラス": "GLASSES / SUNGLASSES",
    "他の": "OTHER",
    "化粧品": "COSMETICS",
    "時計": "WATCH",
    "服": "CLOTHES",
    "靴": "SHOES",
    "高級ジュエリー": "FINE JEWELRY",
}

# 「指定なし」を含むカテゴリ選択肢の表示用英訳(format_func 用)。
# ※ selectbox の内部値・履歴保存・照合はすべて CATEGORY_OPTIONS(日本語)のまま。
#    表示だけ「日本語 / English」併記にして、クメール語/英語環境のstaffに手がかりを出す。
CATEGORY_LABEL_EN = dict(CATEGORY_EN_MAP)
CATEGORY_LABEL_EN["指定なし"] = "None"


def _category_display(value: str) -> str:
    """カテゴリ選択肢の表示文字列。内部値(日本語)は変えず、表示だけ英語を併記する。"""
    en = CATEGORY_LABEL_EN.get(value)
    if en and en != value:
        return f"{value} / {en}"
    return value

# ブランドマスタの category 表記 → カテゴリ選択肢 へのマッピング
# (既存ブランドマスタの category 表記揺れを吸収するため)
BRAND_CATEGORY_NORMALIZE = {
    "バッグ": "バッグ",
    "時計": "時計",
    "ジュエリー": "ジュエリー",
    "アパレル": "服",
    "シューズ": "靴",
    "電子機器": "他の",
    "ステーショナリー": "他の",
}

# Streamlit Session Stateでデータディレクトリを保持
if "data_dir" not in st.session_state:
    st.session_state.data_dir = DEFAULT_DATA_DIR

# 言語設定 (v0.9〜)
# 現在は ja のみ運用、km は将来追加予定。未翻訳キーは ja にフォールバック。
if "lang" not in st.session_state:
    st.session_state.lang = "ja"

# ============================================================
# 多言語メッセージ辞書 (v0.11: ja/en/km の3言語対応)
# ============================================================
# セリフ・UIラベルは messages.py に外出し(staff確定の対訳シートから生成)。
# 構造: MESSAGES[lang][key]。lang = "ja" | "en" | "km"。
# 未翻訳キーは t() が ja にフォールバックする。
# キー体系: ui.* (UIラベル) / msg.* (固定セリフ) / dyn.* (動的セリフ・.formatで変数差し込み)
# HTMLタグ(<b>等)は辞書には含めず、呼び出し側で付与する。
from messages import MESSAGES
from data_i18n import td

# v0.10以前は year_recent 等のプレフィックス無しキーを使用していた。
# 現行辞書は msg.year_recent 等に統一済み。後方互換のため別名を吸収する。
_LEGACY_KEY_ALIAS = {
    "year_recent": "msg.year_recent",
    "year_semi_new": "msg.year_semi_new",
    "year_mid": "msg.year_mid",
    "year_old": "msg.year_old",
    "year_microchip": "msg.year_microchip",
    "year_unknown": "msg.year_unknown",
    "year_random_serial": "msg.year_random_serial",
    "iconic_match": "msg.iconic_match",
}


def t(key: str, **kwargs) -> str:
    """言語切替対応のメッセージ取得。
    - 現在の言語(st.session_state.lang)で引き、無ければ ja にフォールバック。
    - 旧キー(プレフィックス無し)も _LEGACY_KEY_ALIAS 経由で解決。
    - kwargs を渡すと .format() で動的変数を差し込む(dyn.* 用)。
    """
    key = _LEGACY_KEY_ALIAS.get(key, key)
    lang = st.session_state.get("lang", "ja")
    text = MESSAGES.get(lang, {}).get(key)
    if not text:
        text = MESSAGES["ja"].get(key, "")
    if kwargs and text:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # 変数差し込みに失敗しても素のテキストを返す(画面を落とさない)
            pass
    return text


# v0.10以前との後方互換: 旧名 tr() を t() のエイリアスとして残す
def tr(key: str) -> str:
    """[非推奨] t() を使うこと。旧コード互換のために残置。"""
    return t(key)


def get_year_bucket(year_str: str) -> str:
    """製造年から年式バケットを判定。
    現在年を基準に: 直近2年=recent / 3-5年=semi_new / 6-10年=mid / 11年以上=old
    判定不可は空文字。
    """
    if not year_str:
        return ""
    try:
        y = int(str(year_str).strip())
    except (ValueError, TypeError):
        return ""
    current_year = datetime.now().year
    age = current_year - y
    if age < 0:
        return ""  # 未来年は無視
    if age <= 2:
        return "recent"
    elif age <= 5:
        return "semi_new"
    elif age <= 10:
        return "mid"
    else:
        return "old"


def check_iconic_model(product_name: str, iconic_models_str: str) -> bool:
    """品名に定番モデルキーワードが含まれているかチェック (大文字小文字無視)。"""
    if not product_name or not iconic_models_str:
        return False
    name_upper = str(product_name).upper()
    keywords = [k.strip().upper() for k in str(iconic_models_str).split(",") if k.strip()]
    return any(kw in name_upper for kw in keywords)


def get_data_dir() -> Path:
    return Path(st.session_state.data_dir)


# ============================================================
# CSVファイルパス
# ============================================================
def brands_csv() -> Path:
    return get_data_dir() / "brands.csv"

def checklist_csv() -> Path:
    return get_data_dir() / "checklists.csv"

def feedback_csv() -> Path:
    return get_data_dir() / "feedback.csv"

def history_csv() -> Path:
    return get_data_dir() / "appraisal_history.csv"

def keyword_requirements_csv() -> Path:
    """ブランド×カテゴリ別の必要キーワード表(v0.12.3で追加)。
    無くてもアプリは動く(評点機能側でフォールバック)。"""
    return get_data_dir() / "keyword_requirements.csv"

def staff_master_csv() -> Path:
    """staff名マスタ(v0.12.4で追加)。
    staff名のフリーテキスト入力による表記ゆれを防ぐため、選択式の元データとして持つ。
    列は staff_name の1列のみ。無ければ初期値 Komatsu で自動生成する。"""
    return get_data_dir() / "staff_master.csv"

def screenshots_dir() -> Path:
    return get_data_dir() / "screenshots"

def cost_params_path() -> Path:
    return get_data_dir() / "cost_params.json"


# ============================================================
# Eco Ring ブランドマスタ初期データ
# ============================================================
DEFAULT_BRANDS = pd.DataFrame([
    # ア行
    {"brand_ja": "アイ・ダブリュー・シー", "brand_en": "IWC", "category": "時計", "cost_ratio_min": 68, "cost_ratio_max": 73, "notes": "型番・シリアル・年式で相場が大きく変動。書類有無で評価差。", "iconic_models": "PORTOFINO,PORTUGIESER,PILOT,ポートフィノ,ポルトギーゼ,パイロット"},
    {"brand_ja": "アイグナー", "brand_en": "AIGNER", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "国内需要は限定的。状態が良くないと値がつきづらい。", "iconic_models": ""},
    {"brand_ja": "アップル", "brand_en": "APPLE", "category": "電子機器", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "型番・容量・カラー・付属品で大きく変動。アクティベーション要確認。", "iconic_models": ""},
    {"brand_ja": "アニエスベー", "brand_en": "AGNES B", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "カジュアルライン。状態勝負。", "iconic_models": ""},
    {"brand_ja": "アルマーニ", "brand_en": "ARMANI", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "EAとGAはライン違い。年式古いものは値崩れ早い。", "iconic_models": ""},
    {"brand_ja": "アレキサンダー・マックイーン", "brand_en": "ALEXANDER MCQUEEN", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "スカル系は安定需要。状態とトレンド両軸で見る。", "iconic_models": "SKULL,DE MANTA,スカル,デ・マンタ"},
    {"brand_ja": "アレキサンダー・ワン", "brand_en": "ALEXANDER WANG", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "ロッコー系は中古でも回転良。レザーの状態確認。", "iconic_models": ""},
    {"brand_ja": "アンテプリマ", "brand_en": "ANTEPRIMA", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ワイヤーバッグの絡まり・歪みを必ず確認。", "iconic_models": ""},
    {"brand_ja": "イヴ・サンローラン", "brand_en": "YSL", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "サンローラン期/YSL期で価値変動。ロゴデザイン要確認。", "iconic_models": "MUSE,SAC DE JOUR,LOULOU,KATE,ミューズ,サックドジュール,ルル,ケイト"},
    {"brand_ja": "ヴァシュロン・コンスタンタン", "brand_en": "VACHERON CONSTANTIN", "category": "時計", "cost_ratio_min": 72, "cost_ratio_max": 77, "notes": "高級時計。書類・付属品の有無が査定に大きく影響。", "iconic_models": "OVERSEAS,PATRIMONY,オーヴァーシーズ,パトリモニー"},
    {"brand_ja": "ヴァレクストラ", "brand_en": "VALEXTRA", "category": "バッグ", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "イタリア製、レザーの状態勝負。傷・スレに注意。", "iconic_models": "ISIDE,BRERA,イジィデ,ブレラ"},
    {"brand_ja": "ヴァレンティノ", "brand_en": "VALENTINO", "category": "バッグ", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "ロックスタッズの欠け・ハゲは大幅減額。", "iconic_models": "ROCKSTUD,VLOGO,ロックスタッズ,Vロゴ"},
    {"brand_ja": "ヴァン・クリーフ&アーペル", "brand_en": "VAN CLEEF & ARPELS", "category": "ジュエリー", "cost_ratio_min": 68, "cost_ratio_max": 73, "notes": "アルハンブラ系定番。鑑定書・刻印で真贋確認。", "iconic_models": "ALHAMBRA,FRIVOLE,PERLEE,アルハンブラ,フリヴォル,ペルレ"},
    {"brand_ja": "ヴェルサーチェ", "brand_en": "VERSACE", "category": "アパレル", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "メデューサロゴの状態確認。年式古いと需要少。", "iconic_models": ""},
    {"brand_ja": "ウブロ", "brand_en": "HUBLOT", "category": "時計", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "ビッグバン系定番。ベゼル・ベルトの傷み確認。", "iconic_models": "BIG BANG,CLASSIC FUSION,ビッグバン,クラシックフュージョン"},
    {"brand_ja": "エトロ", "brand_en": "ETRO", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ペイズリー柄の退色注意。需要は限定的。", "iconic_models": ""},
    {"brand_ja": "エムシーエム", "brand_en": "MCM", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "復刻ブランド。年代で相場差。", "iconic_models": ""},
    {"brand_ja": "エルメス", "brand_en": "HERMES", "category": "バッグ", "cost_ratio_min": 75, "cost_ratio_max": 80, "notes": "バーキン/ケリーは別格。エブリンは年式・サイズで大きく変動。年式刻印は必ず確認。", "iconic_models": "BIRKIN,KELLY,CONSTANCE,PICOTIN,GARDEN PARTY,EVELYNE,LINDY,バーキン,ケリー,コンスタンス,ピコタン,ガーデンパーティ,エブリン,リンディ"},
    {"brand_ja": "エンポリオ・アルマーニ", "brand_en": "EMPORIO ARMANI", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "EA Lineは比較的回転良。状態勝負。", "iconic_models": ""},
    {"brand_ja": "オーデマ・ピゲ", "brand_en": "AUDEMARS PIGUET", "category": "時計", "cost_ratio_min": 78, "cost_ratio_max": 83, "notes": "ロイヤルオークが定番高級時計。書類・付属品マスト。", "iconic_models": "ROYAL OAK,ロイヤルオーク"},
    {"brand_ja": "オフホワイト", "brand_en": "OFF-WHITE", "category": "アパレル", "cost_ratio_min": 35, "cost_ratio_max": 40, "notes": "サイクル早いブランド。最新コレクションかどうかで値崩れ大。", "iconic_models": ""},
    {"brand_ja": "オリエント", "brand_en": "ORIENT", "category": "時計", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "国産時計。型番で価値分岐。", "iconic_models": ""},
    {"brand_ja": "オリス", "brand_en": "ORIS", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "スイス時計。状態と書類で評価。", "iconic_models": ""},
    # カ行
    {"brand_ja": "カシオ", "brand_en": "CASIO", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "Gショック系は型番で大きく変動。レア・コラボ要注意。", "iconic_models": ""},
    {"brand_ja": "カルティエ", "brand_en": "CARTIER", "category": "ジュエリー", "cost_ratio_min": 68, "cost_ratio_max": 73, "notes": "ラブ/トリニティは定番。素材(YG/WG/PG)で相場差。鑑定書要確認。", "iconic_models": "LOVE,TRINITY,JUSTE UN CLOU,PANTHERE,TANK,SANTOS,ラブ,トリニティ,ジュストアンクル,パンテール,タンク,サントス"},
    {"brand_ja": "クリスチャン・ルブタン", "brand_en": "LOUBOUTIN", "category": "シューズ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "赤底のスレ・剥がれは減額大。サイズ需要も影響。", "iconic_models": "PIK PIK,SO KATE,PIGALLE,ピックピック,ソーケイト,ピガール"},
    {"brand_ja": "クロエ", "brand_en": "CHLOE", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "パディントン・パラティ系は定番。金具のメッキ確認。", "iconic_models": "PADDINGTON,PARATY,DREW,MARCIE,FAYE,パディントン,パラティ,ドリュー,マーシー,フェイ"},
    {"brand_ja": "グッチ", "brand_en": "GUCCI", "category": "バッグ", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "GG柄は時代で価値変動。新作は値崩れ早い傾向。", "iconic_models": "JACKIE,BAMBOO,DIONYSUS,GG MARMONT,SOHO,ジャッキー,バンブー,ディオニュソス,マーモント,ソーホー"},
    {"brand_ja": "ケイト・スペード", "brand_en": "KATE SPADE", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "カジュアル価格帯。状態勝負。", "iconic_models": ""},
    {"brand_ja": "ケンゾー", "brand_en": "KENZO", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "タイガーロゴ系は安定需要。", "iconic_models": ""},
    {"brand_ja": "コーチ", "brand_en": "COACH", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "アウトレットラインと正規ラインで相場差大。型番要確認。", "iconic_models": "TABBY,WILLOW,ROGUE,DREAMER,タビー,ウィロー,ローグ,ドリーマー"},
    {"brand_ja": "コム デ ギャルソン", "brand_en": "COMME DES GARCONS", "category": "アパレル", "cost_ratio_min": 35, "cost_ratio_max": 40, "notes": "プレイラインは安定需要。コレクション物は別途。", "iconic_models": ""},
    {"brand_ja": "コルム", "brand_en": "CORUM", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "アドミラルカップが定番。状態勝負。", "iconic_models": ""},
    # サ行
    {"brand_ja": "ジバンシィ", "brand_en": "GIVENCHY", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "アンティゴナが定番。レザーの状態が決め手。", "iconic_models": "ANTIGONA,PANDORA,アンティゴナ,パンドラ"},
    {"brand_ja": "ジミー・チュウ", "brand_en": "JIMMY CHOO", "category": "シューズ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "サンダル・パンプス系。ヒール部分の傷み確認。", "iconic_models": "ROMY,LOVE,ANOUK,ロミー,ラブ"},
    {"brand_ja": "ジャガー・ルクルト", "brand_en": "JAEGER LECOULTRE", "category": "時計", "cost_ratio_min": 62, "cost_ratio_max": 67, "notes": "レベルソが定番。状態・書類で評価。", "iconic_models": "REVERSO,MASTER,レベルソ,マスター"},
    {"brand_ja": "ジャスティン・デイビス", "brand_en": "JUSTIN DAVIS", "category": "ジュエリー", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "シルバー925素材。クロス系需要。", "iconic_models": ""},
    {"brand_ja": "ジル・サンダー", "brand_en": "JIL SANDER", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ミニマル系。状態勝負、年式古いと需要減。", "iconic_models": ""},
    {"brand_ja": "ジョルジオ・アルマーニ", "brand_en": "GIORGIO ARMANI", "category": "アパレル", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "GAライン。EAより上位。状態と年式で評価。", "iconic_models": ""},
    {"brand_ja": "シャネル", "brand_en": "CHANEL", "category": "バッグ", "cost_ratio_min": 65, "cost_ratio_max": 70, "notes": "マトラッセ系はシリアル要確認。素材(キャビア/ラム)で大差。年代でシリアル形式が変わる。", "iconic_models": "MATELASSE,CLASSIC,BOY,GABRIELLE,19,DEAUVILLE,マトラッセ,クラシック,ボーイ,ガブリエル,ドーヴィル"},
    {"brand_ja": "ショパール", "brand_en": "CHOPARD", "category": "ジュエリー", "cost_ratio_min": 62, "cost_ratio_max": 67, "notes": "ハッピーダイヤ系。鑑定書要確認。", "iconic_models": "HAPPY DIAMONDS,HAPPY SPORT,HAPPY HEARTS,ハッピーダイヤ,ハッピースポーツ,ハッピーハート"},
    {"brand_ja": "スワロフスキー", "brand_en": "SWAROVSKI", "category": "ジュエリー", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "クリスタル素材。状態で評価大きく変動。", "iconic_models": ""},
    {"brand_ja": "ステラ・マッカートニー", "brand_en": "STELLA MCCARTNEY", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "ファラベラが定番。エコレザーの劣化に注意。", "iconic_models": "FALABELLA,FRAYME,ファラベラ,フレイム"},
    {"brand_ja": "セイコー", "brand_en": "SEIKO", "category": "時計", "cost_ratio_min": 40, "cost_ratio_max": 45, "notes": "GS/グランドセイコーは別格。型番で相場大差。", "iconic_models": ""},
    {"brand_ja": "セリーヌ", "brand_en": "CELINE", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "ラゲージ・トリオンフ系定番。フィービー期/エディ期で価値変動。", "iconic_models": "LUGGAGE,TRIOMPHE,CLASSIC,BELT,16,SIXTEEN,ラゲージ,トリオンフ,クラシック,ベルト"},
    # タ行
    {"brand_ja": "タグ・ホイヤー", "brand_en": "TAG HEUER", "category": "時計", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "カレラ・モナコ系定番。状態と書類で評価。", "iconic_models": "CARRERA,MONACO,AQUARACER,カレラ,モナコ,アクアレーサー"},
    {"brand_ja": "ダイアン・フォン・ファステンバーグ", "brand_en": "DIANE VON FURSTENBERG", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ラップドレス系。需要は限定的。", "iconic_models": ""},
    {"brand_ja": "ダンヒル", "brand_en": "DUNHILL", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "メンズ需要中心。レザー状態が決め手。", "iconic_models": ""},
    {"brand_ja": "チューダー", "brand_en": "TUDOR", "category": "時計", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "ロレックス姉妹ブランド。型番・年式重要。", "iconic_models": "BLACK BAY,PELAGOS,ブラックベイ,ペラゴス"},
    {"brand_ja": "ティソ", "brand_en": "TISSOT", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "スイス時計エントリー。状態勝負。", "iconic_models": ""},
    {"brand_ja": "ティファニー", "brand_en": "TIFFANY", "category": "ジュエリー", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "オープンハート/Tシリーズ定番。素材(SV/YG)で相場差。", "iconic_models": "T,OPEN HEART,RETURN TO,KEY,KNOT,オープンハート,リターントゥ,キー,ノット"},
    {"brand_ja": "ディーケーエヌワイ", "brand_en": "DKNY", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "カジュアル価格帯。状態勝負。", "iconic_models": ""},
    {"brand_ja": "ディオール", "brand_en": "DIOR", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "レディディオール・サドル定番。年代で相場大差。", "iconic_models": "LADY,SADDLE,BOOK TOTE,30 MONTAIGNE,BOBBY,レディ,サドル,ブックトート,モンテーニュ,ボビー"},
    {"brand_ja": "デルヴォー", "brand_en": "DELVAUX", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "ベルギー王室御用達。ブリヨン定番。状態勝負。", "iconic_models": "BRILLANT,TEMPETE,ブリヨン,テンペット"},
    {"brand_ja": "ドルチェ&ガッバーナ", "brand_en": "DOLCE & GABBANA", "category": "アパレル", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "シシリー系バッグも需要あり。状態勝負。", "iconic_models": ""},
    {"brand_ja": "トッズ", "brand_en": "TODS", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "ディーバッグ系。レザーの傷み確認。", "iconic_models": "D BAG,DI BAG,ディーバッグ"},
    {"brand_ja": "トリー・バーチ", "brand_en": "TORY BURCH", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ロゴ金具のメッキ剥がれ要確認。", "iconic_models": ""},
    {"brand_ja": "トゥミ", "brand_en": "TUMI", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "ビジネス需要中心。型番・状態で評価。", "iconic_models": ""},
    # ハ行
    {"brand_ja": "バーバリー", "brand_en": "BURBERRY", "category": "アパレル", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "チェック柄定番。年式・素材で価値分岐。", "iconic_models": ""},
    {"brand_ja": "バリー", "brand_en": "BALLY", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "スイス老舗。レザーの状態勝負。", "iconic_models": ""},
    {"brand_ja": "バレンシアガ", "brand_en": "BALENCIAGA", "category": "バッグ", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "シティ・ヴィル系定番。タッセルの状態確認。", "iconic_models": "CITY,VILLE,LE CAGOLE,HOURGLASS,シティ,ヴィル,カゴール,アワーグラス"},
    {"brand_ja": "パテック・フィリップ", "brand_en": "PATEK PHILIPPE", "category": "時計", "cost_ratio_min": 82, "cost_ratio_max": 87, "notes": "高級時計の頂点。書類・付属品マスト。", "iconic_models": "NAUTILUS,CALATRAVA,AQUANAUT,ノーチラス,カラトラバ,アクアノート"},
    {"brand_ja": "パネライ", "brand_en": "PANERAI", "category": "時計", "cost_ratio_min": 62, "cost_ratio_max": 67, "notes": "ルミノール・ラジオミール定番。型番重要。", "iconic_models": "LUMINOR,RADIOMIR,ルミノール,ラジオミール"},
    {"brand_ja": "ピアジェ", "brand_en": "PIAGET", "category": "時計", "cost_ratio_min": 62, "cost_ratio_max": 67, "notes": "ジュエリーウォッチ系。状態と素材で評価。", "iconic_models": "POSSESSION,LIMELIGHT,ポセション,ライムライト"},
    {"brand_ja": "フェラガモ", "brand_en": "FERRAGAMO", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "ガンチーニ金具のメッキ剥がれ要確認。", "iconic_models": ""},
    {"brand_ja": "フェンディ", "brand_en": "FENDI", "category": "バッグ", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "ピーカブー・バゲット定番。年代で価値分岐。", "iconic_models": "PEEKABOO,BAGUETTE,KAN I,SUNSHINE,ピーカブー,バゲット,カン"},
    {"brand_ja": "フォレ・ル・パージュ", "brand_en": "FAURE LE PAGE", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "パリ老舗。需要は限定的だがコレクター人気。", "iconic_models": ""},
    {"brand_ja": "フランク・ミュラー", "brand_en": "FRANCK MULLER", "category": "時計", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "トノーカーベックス定番。書類重要。", "iconic_models": "TONNEAU,LONG ISLAND,トノー,ロングアイランド"},
    {"brand_ja": "プラダ", "brand_en": "PRADA", "category": "バッグ", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "サフィアーノは状態で評価大きく変わる。ナイロンはカンボジア需要少。", "iconic_models": "GALLERIA,RE-EDITION,CAHIER,DOUBLE,ガレリア,リエディション,カイエ,ダブルバッグ"},
    {"brand_ja": "ブライトリング", "brand_en": "BREITLING", "category": "時計", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "ナビタイマー・スーパーオーシャン定番。書類重要。", "iconic_models": "NAVITIMER,SUPEROCEAN,AVENGER,ナビタイマー,スーパーオーシャン,アベンジャー"},
    {"brand_ja": "ブラウン・ビュッフェル", "brand_en": "BRAUN BUFFEL", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ドイツブランド。需要は限定的。", "iconic_models": ""},
    {"brand_ja": "ブルガリ", "brand_en": "BVLGARI", "category": "ジュエリー", "cost_ratio_min": 62, "cost_ratio_max": 67, "notes": "セルペンティ・ビーゼロワン定番。素材で相場差。", "iconic_models": "B.ZERO1,SERPENTI,DIVAS DREAM,BVLGARI BVLGARI,ビーゼロワン,セルペンティ,ディーヴァ"},
    {"brand_ja": "ブレゲ", "brand_en": "BREGUET", "category": "時計", "cost_ratio_min": 68, "cost_ratio_max": 73, "notes": "クラシック高級時計。書類・状態で評価。", "iconic_models": ""},
    {"brand_ja": "プロエンザ・スクーラー", "brand_en": "PROENZA SCHOULER", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "PS1系定番。需要は限定的。", "iconic_models": ""},
    {"brand_ja": "ベルルッティ", "brand_en": "BERLUTI", "category": "シューズ", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "パティーヌレザーが特徴。状態勝負。", "iconic_models": "ALESSANDRO,LORENZO,アレッサンドロ,ロレンツォ"},
    {"brand_ja": "ベル&ロス", "brand_en": "BELL & ROSS", "category": "時計", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "スクエア型ミリタリーウォッチ。状態と書類で評価。", "iconic_models": ""},
    {"brand_ja": "ボーム&メルシエ", "brand_en": "BAUME & MERCIER", "category": "時計", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "クラシエマ定番。状態勝負。", "iconic_models": ""},
    {"brand_ja": "ボール", "brand_en": "BALL", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "鉄道時計の老舗。型番で評価。", "iconic_models": ""},
    {"brand_ja": "ボッテガ・ヴェネタ", "brand_en": "BOTTEGA VENETA", "category": "バッグ", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "イントレチャート系定番。レザー状態勝負。", "iconic_models": "INTRECCIATO,POUCH,CASSETTE,JODIE,イントレチャート,ポーチ,カセット,ジョディ"},
    # マ行
    {"brand_ja": "マーク・ジェイコブス", "brand_en": "MARC JACOBS", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "スナップショット系定番。状態勝負。", "iconic_models": ""},
    {"brand_ja": "マーク・バイ・マーク・ジェイコブス", "brand_en": "MARC BY MARC JACOBS", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "セカンドライン。本家より相場低め。", "iconic_models": ""},
    {"brand_ja": "マイケル・コース", "brand_en": "MICHAEL KORS", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "アウトレット流通も多い。型番要確認。", "iconic_models": ""},
    {"brand_ja": "マックスマーラ", "brand_en": "MAX MARA", "category": "アパレル", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "コート系で需要。状態勝負。", "iconic_models": ""},
    {"brand_ja": "マルニ", "brand_en": "MARNI", "category": "バッグ", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "トランクバッグ系定番。状態勝負。", "iconic_models": "TRUNK,MUSEO,トランク,ムゼオ"},
    {"brand_ja": "マルベリー", "brand_en": "MULBERRY", "category": "バッグ", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "ベイズウォーター定番。レザー状態勝負。", "iconic_models": "BAYSWATER,LILY,ALEXA,ベイズウォーター,リリー,アレクサ"},
    {"brand_ja": "ミキモト", "brand_en": "MIKIMOTO", "category": "ジュエリー", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "真珠の老舗。鑑定書・素材で評価。", "iconic_models": "MIKIMOTO,パール,真珠"},
    {"brand_ja": "モスキーノ", "brand_en": "MOSCHINO", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ロゴ・キャラ系で需要分岐。", "iconic_models": ""},
    {"brand_ja": "モワナ", "brand_en": "MOYNAT", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "パリ老舗。需要は限定的だが高評価。", "iconic_models": ""},
    {"brand_ja": "モンブラン", "brand_en": "MONTBLANC", "category": "ステーショナリー", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "万年筆主流。レザーグッズも展開。", "iconic_models": ""},
    # ヤ行
    {"brand_ja": "ユリス・ナルダン", "brand_en": "ULYSSE NARDIN", "category": "時計", "cost_ratio_min": 58, "cost_ratio_max": 63, "notes": "マリン系定番。書類重要。", "iconic_models": ""},
    {"brand_ja": "ヨウジヤマモト", "brand_en": "YOHJI YAMAMOTO", "category": "アパレル", "cost_ratio_min": 32, "cost_ratio_max": 37, "notes": "ブラックライン中心。コレクション物は別途。", "iconic_models": ""},
    # ラ行
    {"brand_ja": "ラドー", "brand_en": "RADO", "category": "時計", "cost_ratio_min": 38, "cost_ratio_max": 43, "notes": "セラミック素材定番。状態勝負。", "iconic_models": ""},
    {"brand_ja": "ラルフ・ローレン", "brand_en": "RALPH LAUREN", "category": "アパレル", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "ポロライン主力。年式で需要分岐。", "iconic_models": ""},
    {"brand_ja": "ルイ・ヴィトン", "brand_en": "LOUIS VUITTON", "category": "バッグ", "cost_ratio_min": 52, "cost_ratio_max": 57, "notes": "モノグラム/ダミエは安定。エピやヴェルニは色によって相場差大。", "iconic_models": "SPEEDY,NEVERFULL,ALMA,CAPUCINES,KEEPALL,POCHETTE,ON THE GO,TWIST,スピーディ,ネヴァーフル,アルマ,カプシーヌ,キーポル,ポシェット,オンザゴー,ツイスト"},
    {"brand_ja": "レベッカ・ミンコフ", "brand_en": "REBECCA MINKOFF", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "需要は限定的。", "iconic_models": ""},
    {"brand_ja": "ロエベ", "brand_en": "LOEWE", "category": "バッグ", "cost_ratio_min": 48, "cost_ratio_max": 53, "notes": "パズル・ハンモック定番。レザーの状態勝負。", "iconic_models": "PUZZLE,HAMMOCK,GATE,AMAZONA,パズル,ハンモック,ゲート,アマソナ"},
    {"brand_ja": "ロレックス", "brand_en": "ROLEX", "category": "時計", "cost_ratio_min": 80, "cost_ratio_max": 85, "notes": "型番・年式・ギャランティ有無で相場が大きく変動。書類確認必須。シリアルから年式判定可能(2010以前)。", "iconic_models": "SUBMARINER,DAYTONA,GMT,DATEJUST,EXPLORER,YACHT MASTER,SEA-DWELLER,サブマリーナ,デイトナ,デイトジャスト,エクスプローラー,ヨットマスター,シードゥエラー"},
    {"brand_ja": "ロンシャン", "brand_en": "LONGCHAMP", "category": "バッグ", "cost_ratio_min": 28, "cost_ratio_max": 33, "notes": "プリアージュ定番。状態勝負。", "iconic_models": "LE PLIAGE,ROSEAU,プリアージュ,ロゾー"},
    {"brand_ja": "ロンジン", "brand_en": "LONGINES", "category": "時計", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "クラシック時計。状態と書類で評価。", "iconic_models": ""},
    # 英記号系
    {"brand_ja": "U-ボート", "brand_en": "U-BOAT", "category": "時計", "cost_ratio_min": 42, "cost_ratio_max": 47, "notes": "イタリアン大型時計。需要は限定的。", "iconic_models": ""},
])

# ============================================================
# Eco Ring チェックリスト初期データ
# ============================================================
DEFAULT_CHECKLISTS = pd.DataFrame([
    # ルイ・ヴィトン
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "ヌメ革の焼け・シミ", "hint": "未使用品でも経年で焼ける。色味で年代感分かる。"},
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "四隅のスレ・革剥がれ", "hint": "B+ → B 降格の最頻要因。光に当てて確認。"},
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "持ち手の汚れ・テカリ", "hint": "使用頻度を示す。手垢の黒ずみは減額対象。"},
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "内側の汚れ・ベタつき", "hint": "高湿度環境(東南アジア)では特に注意。剥がれは修理高額。"},
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "金具のスレ・メッキ剥がれ", "hint": "真鍮露出があればB→B-級の判定材料。"},
    {"brand_ja": "ルイ・ヴィトン", "category": "バッグ", "check_item": "型番(品番)の確認", "hint": "底面/内側ポケットに刻印。年式特定の鍵。"},
    # エルメス
    {"brand_ja": "エルメス", "category": "バッグ", "check_item": "刻印(製造年)の確認", "hint": "アルファベットと囲みのスタイルで年代特定可能。Chosukeに年式を入力すると詳細案内します。"},
    {"brand_ja": "エルメス", "category": "バッグ", "check_item": "金具の傷・ハゲ", "hint": "ゴールド/シルバー金具は特に減額大。"},
    {"brand_ja": "エルメス", "category": "バッグ", "check_item": "付属品(鍵/ロック/レインカバー)", "hint": "鍵が紛失していても鍵単体の相場もあるので確認してみて。クロシェットも要確認。"},
    # シャネル
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "シリアルシールの確認", "hint": "シール剥がれ/シール無は要警戒。桁数(7桁/8桁)で年代分岐。"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "シールのブラックライト発光確認", "hint": "ブラックライトを当てて、正規の発光パターンが出るか確認。"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "ロゴの字体確認", "hint": "CHANELロゴの形・間隔・太さに違和感はないか?"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "縫製の確認", "hint": "ステッチの均一性・歪み・ほつれがないか。"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "ルーペでの細部確認", "hint": "肉眼で見にくいポイント(金具刻印・ステッチ等)はルーペを使ったか?"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "内部の汚れ確認", "hint": "ライトを使って内ポケット・底面の汚れ・シミを確認したか?"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "チェーンの状態", "hint": "メッキ剥がれ・伸び・絡みを確認。"},
    {"brand_ja": "シャネル", "category": "バッグ", "check_item": "ココマークの状態", "hint": "メッキハゲ・歪みは減額対象。"},
    # グッチ
    {"brand_ja": "グッチ", "category": "バッグ", "check_item": "シリアルナンバーの確認", "hint": "内側タグ。GGキャンバスは比較的相場安定。"},
    # プラダ
    {"brand_ja": "プラダ", "category": "バッグ", "check_item": "ナイロン部分の傷み", "hint": "ナイロンはカンボジア需要少。素材で買取判断分岐。"},
    # ロレックス
    {"brand_ja": "ロレックス", "category": "時計", "check_item": "ギャランティカードの有無", "hint": "あれば+20-30%評価。なしは要警戒。"},
    {"brand_ja": "ロレックス", "category": "時計", "check_item": "型番/シリアル/年式", "hint": "型番で本体相場が決まる。シリアルから年式判定可能(2010以前)。Chosukeにシリアル先頭を入力すると年代推定します。"},
    {"brand_ja": "ロレックス", "category": "時計", "check_item": "ベゼル・風防の傷", "hint": "ポリッシュで取れる範囲か、要相談。"},
    {"brand_ja": "ロレックス", "category": "時計", "check_item": "稼働状態", "hint": "オーバーホール費用(数万円)を考慮した買取になる。"},
    # カルティエ
    {"brand_ja": "カルティエ", "category": "ジュエリー", "check_item": "刻印(750/Au750/PT950)", "hint": "素材確定はジュエリー相場の出発点。"},
    {"brand_ja": "カルティエ", "category": "ジュエリー", "check_item": "ダイヤ/石の有無と状態", "hint": "石抜けは大幅減額。鑑定書あれば+評価。"},
    {"brand_ja": "カルティエ", "category": "ジュエリー", "check_item": "サイズ刻印", "hint": "リング系はサイズ需要に影響。"},
])


# ============================================================
# 年式判定ロジック
# ============================================================

def hermes_year_from_stamp(stamp: str) -> str:
    """Hermès刻印から年式を判定。

    ・○囲み期(1971-1996): アルファベット順 ○A=1971…○Z=1996
      → ヴィンテージ品なので「鑑定士に確認」で逃げる方針
    ・□囲み期(1997-2014): アルファベット順 □A=1997…□R=2014
    ・裸期(2014後半-): 順序は特殊なので対応表
    """
    if not stamp:
        return ""
    stamp = stamp.strip().upper()
    has_circle = any(c in stamp for c in ["○", "◯", "(", "(", "[", "「"])
    has_square = any(c in stamp for c in ["□", "[", "「"])
    letter = "".join(c for c in stamp if c.isalpha())
    if not letter:
        return ""
    letter = letter[0]

    # □囲み期: A=1997 〜 R=2014 (アルファベット順)
    square_map = {chr(ord("A") + i): 1997 + i for i in range(18)}  # A〜R

    # 裸期: 2014年後半 R から開始、以降ランダム順
    naked_map = {"R": 2014, "T": 2015, "X": 2016,
                 "A": 2017, "C": 2018, "D": 2019, "Y": 2020, "Z": 2021,
                 "U": 2022, "B": 2023, "W": 2024, "K": 2025, "G": 2026}

    # 囲み形状が明示されている場合
    if has_circle:
        return (f"○{letter} はヴィンテージ品(1971-1996期)です。"
                f"年式の特定や状態評価は鑑定士に確認してください。")

    if has_square:
        if letter in square_map:
            return f"□{letter} → {square_map[letter]}年"
        else:
            return (f"□{letter} は判定表外です(□囲みは A=1997〜R=2014 の範囲)。"
                    f"刻印の読み取りを再確認してください。")

    # 囲み形状が不明な場合: 候補を併記
    candidates = []
    candidates.append(f"○{letter} ならヴィンテージ品(1971-1996期、鑑定士に確認)")
    if letter in square_map:
        candidates.append(f"□{letter} なら {square_map[letter]}年")
    if letter in naked_map:
        candidates.append(f"裸の{letter} なら {naked_map[letter]}年")

    if len(candidates) > 1:
        return " / ".join(candidates) + "  ← 囲みの形状をよく確認してください。"
    return candidates[0] if candidates else f"刻印 '{stamp}' は判定表にありません。"


def chanel_year_from_serial(serial: str) -> str:
    """CHANEL シリアルから年代を判定(社内資料準拠・v0.7で全面修正)。"""
    if not serial:
        return ""
    serial = re.sub(r"\D", "", serial)
    if not serial:
        return ""
    n = len(serial)

    if n == 7 or n == 6:
        # 7桁台(稀に0番台のみ6桁)
        first = int(serial[0])
        seven_map = {
            0: "1985〜1988年前後",
            1: "1989〜1991年前後",
            2: "1991〜1994年前後",
            3: "1994〜1996年前後",
            4: "1994〜1997年前後",
            5: "1997〜1999年前後",
            6: "2000〜2001年前後",
            7: "2001〜2002年前後",
            8: "2003〜2004年前後",
            9: "2004〜2005年前後",
        }
        if first in seven_map:
            digits_note = "(稀に6桁)" if (n == 6 and first == 0) else ""
            return f"{n}桁先頭{first}番台{digits_note}: {seven_map[first]}"

    elif n == 8:
        head2 = int(serial[:2])
        # 社内資料の年代テーブル(重複範囲は幅を持たせて表記)
        ranges = [
            (10, 10, "2005〜2006年前後"),
            (11, 11, "2007〜2008年前後"),
            (12, 12, "2008〜2009年前後"),
            (13, 13, "2009〜2010年前後"),
            (14, 14, "2010〜2011年前後"),
            (15, 15, "2011〜2012年前後"),
            (16, 16, "2012〜2013年前後"),
            (17, 17, "2013〜2014年前後"),
            (18, 20, "2014〜2015年前後"),
            (21, 21, "2015〜2016年前後"),
            (22, 23, "2016〜2017年前後"),
            (24, 25, "2017〜2018年前後"),
            (26, 26, "2018〜2019年前後"),
            (27, 28, "2019〜2020年前後"),
            (29, 29, "2019〜2021年前後(境界・要照合)"),
            (30, 30, "2020〜2021年前後(境界・要照合)"),
            (31, 32, "2021年前後〜"),
        ]
        for lo, hi, year in ranges:
            if lo <= head2 <= hi:
                return f"8桁先頭{head2}番台: {year}"
        if head2 >= 33:
            return ("8桁先頭33以降: 判定表外。"
                    "2021年以降はマイクロチップ化(ランダム番号)が主流のため、"
                    "シリアル番号のみで年式特定は不可。マイクロチップ品の可能性。")

    # 7桁/8桁以外、または非数値混在
    # ランダム番号の可能性チェック(2021年以降のチップ品)
    return (f"シリアル桁数 {n}桁: 判定表外、または非標準形式。"
            "2021年以降のCHANELはマイクロチップ化(ランダム番号)されているため、"
            "シリアルでの年式判定は不可。製造年欄の「マイクロチップ品」にチェックしてください。"
            "それ以外の場合は真贋に注意。")


def rolex_year_from_serial(serial: str) -> str:
    """ROLEX シリアルから年式を判定。"""
    if not serial:
        return ""
    serial = serial.strip().upper()
    if not serial:
        return ""

    if serial.isdigit():
        head2 = int(serial[:2])
        digit_map = [
            (12, 1965), (18, 1966), (21, 1967), (24, 1968), (26, 1969),
            (29, 1970), (32, 1971), (34, 1972), (37, 1973), (40, 1974),
            (42, 1975), (45, 1976), (50, 1977), (54, 1978), (59, 1979),
            (64, 1980), (69, 1981), (73, 1982), (78, 1983), (83, 1984),
            (86, 1985), (92, 1986), (97, 1987), (99, 1987),
        ]
        for n, y in digit_map:
            if head2 == n:
                return f"数字シリアル {head2}: {y}年頃"
        closest = min(digit_map, key=lambda x: abs(x[0] - head2))
        return f"数字シリアル {head2}: {closest[1]}年付近(参考)"

    head_letter = serial[0]
    letter_map = {
        "R": [1987, 1988], "L": [1988, 1990], "E": [1990, 1991],
        "X": [1991], "N": [1991], "C": [1992], "S": [1993],
        "W": [1994], "T": [1995, 1996], "U": [1997, 1998],
        "A": [1999, 2000], "P": [2000, 2001], "K": [2002],
        "Y": [2003], "F": [2004], "D": [2005], "Z": [2006],
        "M": [2007, 2008], "V": [2008, 2009], "G": [2010],
    }
    if head_letter in letter_map:
        years = letter_map[head_letter]
        if len(years) == 1:
            return f"英数字シリアル先頭 {head_letter}: {years[0]}年頃"
        else:
            return f"英数字シリアル先頭 {head_letter}: {years[0]}〜{years[-1]}年頃"

    return "判定表外のシリアル形式。2011年以降のランダム化シリアルの可能性あり、その場合は他の手がかりで年式判断を。"


# ============================================================
# 相場の幅判定ロジック
# ============================================================
def market_range_check(price_min: float, price_max: float) -> dict:
    """相場の幅から、staffの相場感を検証する。"""
    if price_min <= 0 or price_max <= 0:
        return {"level": "unknown", "ratio": 0, "message": ""}
    if price_min > price_max:
        price_min, price_max = price_max, price_min

    ratio = price_max / price_min if price_min > 0 else 0

    if ratio <= 1.15:
        return {
            "level": "narrow", "ratio": ratio,
            "message": t("dyn.range.narrow", ratio=f"{ratio:.2f}")
        }
    elif ratio <= 1.4:
        return {
            "level": "normal", "ratio": ratio,
            "message": t("dyn.range.normal", ratio=f"{ratio:.2f}")
        }
    elif ratio <= 2.0:
        return {
            "level": "wide", "ratio": ratio,
            "message": t("dyn.range.wide", ratio=f"{ratio:.2f}")
        }
    else:
        return {
            "level": "very_wide", "ratio": ratio,
            "message": t("dyn.range.very_wide", ratio=f"{ratio:.2f}")
        }


# ============================================================
# 査定の評点(評価)機能 ※v0.12 プロトタイプ
# ============================================================
# 管理者がレビュー時に参照する客観評点。現場の子の画面には出さない。
# 軸1: 記載の充分さ / 軸2: 金額の幅の絞り込み

@st.cache_data(show_spinner=False)
def load_keyword_requirements() -> dict:
    """必要キーワード表をロード。返り値は (brand_ja, category) -> 要求情報。
       要求情報は {'must':[(kw,match_rule),...], 'want':[(kw,'each'),...]}。
       match_rule: 'each'=個別に必要 / 'any'=同じmustの中でどれか1つあればOK。
       ファイルが無ければ空dictを返す(評点側でフォールバック)。
    """
    req = {}
    df = be.read_sheet("keyword_requirements")
    if df.empty:
        return {}
    for _, row in df.iterrows():
        bj = str(row.get("brand_ja") or "").strip()
        cat = str(row.get("category") or "").strip()
        kw = str(row.get("keyword") or "").strip()
        if not bj or not kw:
            continue
        try:
            imp = int(row.get("importance") or 0)
        except (ValueError, TypeError):
            imp = 0
        match_rule = str(row.get("match_rule") or "each").strip() or "each"
        key = (bj, cat)
        if key not in req:
            req[key] = {"must": [], "want": []}
        if imp == 1:
            req[key]["must"].append((kw, match_rule))
        else:
            req[key]["want"].append((kw, "each"))
    return req


def _cell_str(v) -> str:
    """セル値を安全に文字列化。pandas NaN や None は空文字列に。"""
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    s = str(v).strip()
    if s.lower() == "nan":
        return ""
    return s


def score_completeness(row: dict) -> dict:
    """記載の充分さ。キーワード表(必要キーワード×ブランド×カテゴリ)があれば、
    品名テキストの中身を見て「最重要キーワードが入力されているか」で評価する。
    キーワード表が無い、または該当ブランドが表に無い場合は、入力欄ベースの判定にフォールバック。
    """
    req = load_keyword_requirements()
    brand_ja = _cell_str(row.get("brand_ja"))
    category = _cell_str(row.get("category"))
    product_name = _cell_str(row.get("product_name"))

    # キーワード表ベースの判定が使えるか
    bucket = req.get((brand_ja, category))
    if bucket is None:
        # カテゴリ未登録(査定時に未指定だったケース等)はブランドのみでフォールバック
        for (b, c), v in req.items():
            if b == brand_ja:
                bucket = v
                break

    if bucket and bucket.get("must"):
        # === キーワード表ベース判定 ===
        must = bucket["must"]
        any_items = [kw for kw, rule in must if rule == "any"]
        each_items = [kw for kw, rule in must if rule != "any"]

        missing = []
        # any: どれか1つあればOK
        if any_items:
            if not any(_keyword_evidence(kw, row) for kw in any_items):
                missing.append("最重要(" + " / ".join(any_items) + ")のどれか")
        # each: それぞれ個別に必要
        for kw in each_items:
            if not _keyword_evidence(kw, row):
                missing.append(kw)

        total_must = (1 if any_items else 0) + len(each_items)
        filled = total_must - len(missing)
        # 相場メモは別軸(軸2)で評価するが、最重要に「相場メモ」が含まれる定義は無い前提。
        # 補助情報として「相場メモが空か」も missing に足す(運用上重要なので)。
        pmin = _cell_str(row.get("price_min_usd"))
        pmax = _cell_str(row.get("price_max_usd"))
        if not (pmin and pmax):
            missing.append("相場メモ")
            total_must += 1
        else:
            filled += 1
            total_must += 1

        if filled == total_must:
            label = "充分"
        elif filled >= total_must - 1:
            label = "ほぼ充分"
        elif total_must > 0 and filled >= total_must * 0.5:
            label = "やや不足"
        else:
            label = "不足"
        return {"label": label, "filled": filled, "total": total_must, "missing": missing,
                "mode": "keyword"}

    # === フォールバック: 入力欄ベース判定 ===
    checks = []
    checks.append(("品名", bool(product_name)))
    year_ok = (
        bool(_cell_str(row.get("year")))
        or _cell_str(row.get("is_microchip")) == "Y"
        or _cell_str(row.get("is_year_unknown")) == "Y"
        or _cell_str(row.get("is_random_serial")) == "Y"
    )
    checks.append(("年式", year_ok))
    rank_val = _cell_str(row.get("rank"))
    checks.append(("Rank", bool(rank_val) and rank_val not in ("未選択", "-", "なし")))
    checks.append(("付属品", bool(_cell_str(row.get("accessories")))))
    pmin = _cell_str(row.get("price_min_usd"))
    pmax = _cell_str(row.get("price_max_usd"))
    checks.append(("相場メモ", bool(pmin) and bool(pmax)))
    filled = sum(1 for _, ok in checks if ok)
    total = len(checks)
    missing = [name for name, ok in checks if not ok]
    if filled == total:
        label = "充分"
    elif filled >= total - 1:
        label = "ほぼ充分"
    elif filled >= total * 0.5:
        label = "やや不足"
    else:
        label = "不足"
    return {"label": label, "filled": filled, "total": total, "missing": missing,
            "mode": "fallback"}


# キーワード評価用の補助関数群
_NUMBER_PATTERN = re.compile(r'[A-Z]{1,2}\d{3,}|\d{4,}|[A-Z]\d{2,}')
_SIZE_PATTERN = re.compile(r'\d+\s*(cm|mm|GB|TB|inch|インチ)|サイズ\s*\d+|\b\d{2,3}\b')
_MATERIAL_WORDS = ['レザー','カーフ','キャビア','ラム','カウ','スエード','キャンバス','PVC','ナイロン',
                   'サフィアーノ','エナメル','クロコ','オーストリッチ','パイソン','金','銀','プラチナ',
                   'シルバー','ゴールド','AU750','SS','チタン','セラミック']
_COLOR_WORDS = ['黒','白','赤','青','緑','黄','茶','ベージュ','ピンク','グレー','ブラウン','ネイビー',
                'ブラック','ホワイト','レッド','ブルー','グリーン','イエロー',
                'モカ','カーキ','ワイン','クリーム','オフホワイト']
_HARDWARE_WORDS = ['GHW','SHW','PHW','ゴールド金具','シルバー金具','金金具','銀金具']
_LINE_WORDS = ['モノグラム','ダミエ','アンプラント','エピ','ヴェルニ','タイガ','トリオンフ',
               'マカダム','イントレチャート','マトラッセ','カイエ','GG','GGマーモント',
               'シェブロン','ハバナ','クラシック','スポーツ','プロフェッショナル']


def _classify_keyword(kw: str) -> set:
    """キーワード文字列を「タイプ」に分類する(複数兼任あり)。"""
    types = set()
    if any(t in kw for t in ['型番','リファレンス','番号','シリアル','モデル番号']):
        types.add('number_like')
    if any(t in kw for t in ['名称','特徴']):
        types.add('name_like')
    if '素材' in kw or '金性' in kw:
        types.add('material')
    if '色' in kw and '金具' not in kw:
        types.add('color')
    if '金具' in kw:
        types.add('hardware_color')
    if 'サイズ' in kw or '重さ' in kw or '容量' in kw:
        types.add('size')
    if 'ライン' in kw or '種類' in kw:
        types.add('lineup')
    if '鑑定書' in kw:
        types.add('cert')
    if not types:
        types.add('name_like')
    return types


def _keyword_evidence(kw_text: str, row: dict) -> bool:
    """1つのキーワード要求について、品名等のテキストから充足しているかを判定。
    アプローチB(タイプ別判定): キーワードのタイプを推定し、対応する証拠を品名から探す。
    """
    types = _classify_keyword(kw_text)
    raw = row.get("product_name", "")
    # pandas NaN("nan"文字列化されてしまう) や None を空文字列に
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        text = ""
    else:
        text = str(raw)
        if text.lower() == "nan":
            text = ""
    # 名称系/番号系の合成キーワード("本体の名称/型番"等)は OR 判定
    if 'name_like' in types or 'number_like' in types:
        if 'number_like' in types and _NUMBER_PATTERN.search(text):
            return True
        if 'name_like' in types:
            stripped = re.sub(r'[\d\s\-_/]+', '', text)
            if stripped:
                return True
        return False
    if 'material' in types:
        return any(w in text for w in _MATERIAL_WORDS)
    if 'color' in types:
        return any(w in text for w in _COLOR_WORDS)
    if 'hardware_color' in types:
        return any(w in text for w in _HARDWARE_WORDS)
    if 'size' in types:
        return bool(_SIZE_PATTERN.search(text))
    if 'lineup' in types:
        return any(w in text for w in _LINE_WORDS)
    if 'cert' in types:
        return False
    return False


def score_range(row: dict) -> dict:
    """金額の幅の絞り込み。相場メモの上限÷下限の倍率で評価(既存ロジック流用)。"""
    try:
        pmin = float(_cell_str(row.get("price_min_usd")) or 0)
        pmax = float(_cell_str(row.get("price_max_usd")) or 0)
    except (ValueError, TypeError):
        pmin = pmax = 0
    if pmin <= 0 or pmax <= 0:
        return {"label": "相場メモなし", "ratio": None}
    ratio = pmax / pmin
    if ratio <= 1.15:
        label = "よく絞れている"
    elif ratio <= 1.4:
        label = "許容範囲"
    elif ratio <= 2.0:
        label = "やや広い"
    else:
        label = "広すぎ(要確認)"
    return {"label": label, "ratio": round(ratio, 2)}


# ============================================================
# データ初期化
# ============================================================
def init_data():
    """スプレッドシートの各タブを保証し、空なら初期データを投入する(クラウド版)。
    - タブが無ければ chosuke_backend がヘッダ付きで自動生成。
    - brands / checklists / staff_master が空なら初期値を投入。
    - appraisal_history の不足列は backend.init_backend() が補う。
    ※移行スクリプトで既にデータが入っていれば、空判定に引っかからず上書きしない。"""
    be.init_backend()

    if be.read_sheet("brands").empty:
        be.write_sheet("brands", DEFAULT_BRANDS)

    if be.read_sheet("checklists").empty:
        be.write_sheet("checklists", DEFAULT_CHECKLISTS)

    sm = be.read_sheet("staff_master")
    if sm.empty or "staff_name" not in sm.columns or sm["staff_name"].fillna("").str.strip().eq("").all():
        be.write_sheet("staff_master", pd.DataFrame({
            "staff_name": DEFAULT_STAFF_ROSTER,
            "slack_user_id": [""] * len(DEFAULT_STAFF_ROSTER),
        }))


# ============================================================
# データ読み書き
# ============================================================
def load_brands() -> pd.DataFrame:
    df = be.read_sheet("brands")
    # v0.9: iconic_models 列が無いデータへの後方互換
    if "iconic_models" not in df.columns:
        df["iconic_models"] = ""
    df["iconic_models"] = df["iconic_models"].fillna("").astype(str)
    return df

def save_brands(df: pd.DataFrame):
    be.write_sheet("brands", df)

def load_staff_master() -> list:
    """staff名の一覧を返す(v0.12.4 / クラウド版)。
    staff_master タブが空なら名簿初期値で自動生成する。
    重複・空白・前後スペースを除いて、表示順でソートして返す。"""
    df = be.read_sheet("staff_master")
    if "staff_name" not in df.columns or df.empty:
        be.write_sheet("staff_master", pd.DataFrame({"staff_name": DEFAULT_STAFF_ROSTER}))
        return sorted(DEFAULT_STAFF_ROSTER)
    names = sorted({
        str(s).strip()
        for s in df["staff_name"].fillna("").tolist()
        if str(s).strip()
    })
    return names if names else sorted(DEFAULT_STAFF_ROSTER)

def add_staff_to_master(name: str) -> None:
    """新規staff名をマスタに追記する(v0.12.4 / クラウド版)。
    既存(大文字小文字・前後スペースを無視して一致)があれば追記しない。
    ※管理者のみが呼べるUIに限定する(査定モードからは追加させない)。"""
    name = (name or "").strip()
    if not name:
        return
    # v0.14.0: slack_user_id 列を保持したまま追記する
    df = be.read_sheet("staff_master")
    if "staff_name" not in df.columns or df.empty:
        df = pd.DataFrame({"staff_name": load_staff_master()})
    if "slack_user_id" not in df.columns:
        df["slack_user_id"] = ""
    existing_lower = {str(n).strip().lower() for n in df["staff_name"].fillna("").tolist()}
    if name.lower() in existing_lower:
        return
    new_row = pd.DataFrame({"staff_name": [name], "slack_user_id": [""]})
    be.write_sheet("staff_master", pd.concat([df, new_row], ignore_index=True))


# ============================================================
# v0.14.0: staff の Slack ユーザーID マッピング
# ============================================================
def load_staff_slack_map() -> dict:
    """{staff_name: slack_user_id} の辞書を返す。
    slack_user_id 列が無い古いデータには後方互換で空を返す。"""
    df = be.read_sheet("staff_master")
    if df.empty or "staff_name" not in df.columns or "slack_user_id" not in df.columns:
        return {}
    out = {}
    for _, row in df.iterrows():
        nm = str(row.get("staff_name", "")).strip()
        sid = str(row.get("slack_user_id", "")).strip()
        if nm and sid:
            out[nm] = sid
    return out


def set_staff_slack_id(name: str, slack_id: str) -> None:
    """指定 staff の slack_user_id を更新する(無ければ列を新設)。"""
    name = (name or "").strip()
    df = be.read_sheet("staff_master")
    if "staff_name" not in df.columns or df.empty:
        df = pd.DataFrame({"staff_name": load_staff_master()})
    if "slack_user_id" not in df.columns:
        df["slack_user_id"] = ""
    mask = df["staff_name"].fillna("").astype(str).str.strip().str.lower() == name.lower()
    if mask.any():
        df.loc[mask, "slack_user_id"] = (slack_id or "").strip()
    else:
        df = pd.concat([df, pd.DataFrame(
            {"staff_name": [name], "slack_user_id": [(slack_id or "").strip()]}
        )], ignore_index=True)
    be.write_sheet("staff_master", df)


def send_slack_dm(slack_user_id: str, text: str) -> tuple:
    """Bot token で個人にDMを送る。成功なら (True, "") を返す。
    token 未設定・送信失敗でも例外は投げず (False, 理由) を返す。"""
    slack_user_id = (slack_user_id or "").strip()
    if not slack_user_id:
        return (False, "no_slack_id")
    try:
        token = st.secrets["SLACK_BOT_TOKEN"]
    except Exception:
        return (False, "no_token")
    try:
        import requests
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=utf-8"},
            json={"channel": slack_user_id, "text": text},
            timeout=8,
        )
        data = resp.json()
        if data.get("ok"):
            return (True, "")
        return (False, data.get("error", "unknown_error"))
    except Exception as e:
        return (False, f"exception:{e}")

def load_checklists() -> pd.DataFrame:
    return be.read_sheet("checklists")

def save_checklists(df: pd.DataFrame):
    be.write_sheet("checklists", df)

def load_feedback() -> pd.DataFrame:
    return be.read_sheet("feedback")

def append_feedback(row: dict):
    be.append_row("feedback", row)

def load_history() -> pd.DataFrame:
    return be.read_sheet("appraisal_history")

def append_history(row: dict):
    be.append_row("appraisal_history", row)


# --- v0.14: トレーニング履歴(本格版) ---
def load_training() -> pd.DataFrame:
    return be.read_sheet("training_history")

def append_training(row: dict):
    be.append_row("training_history", row)


# ============================================================
# 推奨原価率の動的算出 (v0.10)
# 設計インサイト #003 / #005 / #006
# シミュレータ(cost_ratio_simulator)が生成した cost_params.json を読み込み、
# ブランド × カテゴリ × Rank × ギャラ × 付属品 × 年式 から推奨レンジを動的算出。
#
# 計算式 (案③ハイブリッド・上限ベース):
#   上限 = ブランド基準値 + カテゴリ補正 + Rank補正 + ギャラ補正 + 付属品補正 + (定番なら+2)
#   下限 = 上限 − 年式幅
#   推奨レンジ = 下限 〜 上限
#
# パラメータが無い/壊れている場合は None を返し、呼び出し側はマスタ素値にフォールバック。
# ============================================================

# 旧ブランドマスタ category 表記 → cost_params のカテゴリ表記 への正規化
# (BRAND_CATEGORY_NORMALIZE と同じ思想。動的算出の主力カテゴリ判定に使う)
COST_CATEGORY_NORMALIZE = {
    "バッグ": "バッグ",
    "時計": "時計",
    "ジュエリー": "ジュエリー",
    "アパレル": "服",
    "シューズ": "靴",
    "電子機器": "他の",
    "ステーショナリー": "他の",
}

# ギャラ補正テーブルの4分類へカテゴリをマップ
def _map_cat_to_gc_group(cat: str) -> str:
    if cat == "時計":
        return "時計"
    if cat in ("高級ジュエリー", "ジュエリー", "ファッションジュエリー"):
        return "ジュエリー"
    if cat == "バッグ":
        return "バッグ"
    return "その他"


def load_cost_params() -> dict:
    """推奨原価率パラメータを読み込む(クラウド版)。
    Secrets の cost_params(JSON文字列 または テーブル)から読む。
    無ければ None を返し、呼び出し側はマスタ素値にフォールバックする。"""
    try:
        raw = st.secrets.get("cost_params", None)
    except Exception:
        raw = None
    if raw is None:
        return None
    try:
        if isinstance(raw, str):
            return json.loads(raw)
        # secrets にテーブルとして入っている場合は dict 化
        return json.loads(json.dumps(dict(raw)))
    except Exception:
        return None


def compute_dynamic_cost_range(
    params: dict,
    brand_en: str,
    master_cat: str,
    assess_cat: str,
    rank: str,
    gc_status: str,
    accessories_status: str,
    is_iconic: bool,
    year_bucket: str,
    master_center: float = None,
) -> dict:
    """推奨原価率を動的算出する。

    Returns: {"low", "high", "upper_breakdown": [...], "width", "ok": bool} or None
    """
    if not params:
        return None

    # --- ブランド基準値 ---
    overrides = params.get("brand_base_overrides", {})
    if brand_en in overrides:
        base = float(overrides[brand_en])
    elif master_center is not None:
        base = float(master_center)
    else:
        return None

    breakdown = [("基準", round(base))]
    upper = base

    # --- カテゴリ補正 (査定カテゴリが主力と違えば下げ) ---
    main_cat = COST_CATEGORY_NORMALIZE.get(master_cat, master_cat)
    cat_corr_table = params.get("category_correction_when_subcategory", {})
    cat_adj = 0
    is_sub_cat = bool(assess_cat) and (assess_cat != "指定なし") and (assess_cat != main_cat)
    if is_sub_cat:
        cat_adj = cat_corr_table.get(assess_cat, 0)
    if cat_adj != 0:
        breakdown.append((f"カテゴリ({assess_cat})", cat_adj))
        upper += cat_adj

    # --- Rank補正 ---
    rank_table = params.get("rank_correction", {})
    rank_adj = rank_table.get(rank, 0)
    if rank_adj != 0:
        breakdown.append((f"Rank({rank})", rank_adj))
        upper += rank_adj

    # --- ギャラ補正 ---
    gc_group = _map_cat_to_gc_group(assess_cat if is_sub_cat else main_cat)
    gc_table = params.get("gc_card_correction_by_category", {})
    gc_adj = 0
    if gc_status == "has":
        gc_adj = gc_table.get(gc_group, {}).get("has", 0)
    elif gc_status == "none":
        gc_adj = gc_table.get(gc_group, {}).get("none", 0)
    if gc_adj != 0:
        breakdown.append(("ギャラ", gc_adj))
        upper += gc_adj

    # --- 付属品補正 ---
    acc_table = params.get("accessories_correction", {})
    # accessories_status は "フルセット"/"一部欠品"/"本体のみ"
    acc_key = accessories_status if accessories_status in acc_table else None
    acc_adj = acc_table.get(acc_key, 0) if acc_key else 0
    if acc_adj != 0:
        breakdown.append(("付属品", acc_adj))
        upper += acc_adj

    # --- 定番ボーナス ---
    iconic_bonus = params.get("iconic_bonus_upper", 2)
    if is_iconic and iconic_bonus:
        breakdown.append(("定番", iconic_bonus))
        upper += iconic_bonus

    # year_bucket (recent/semi_new/mid/old) → cost_params のキーへマップ
    # (年式上限補正・年式幅の両方で共通利用)
    bucket_to_key = {
        "recent": "直近2年 (近年モデル)",
        "semi_new": "3〜5年 (準新作)",
        "mid": "6〜10年 (中堅年式)",
        "old": "10年超 (年代物)",
    }

    # --- 年式上限補正 (v0.10.5: 年式が古いほど天井そのものを下げる) ---
    # 従来は年式が「下限の幅」にしか効かず、新品でも年代物でも上限が同じだった。
    # year_upper_correction を上限計算に加えることで、古い品は天井から下がる。
    upper_corr_table = params.get("year_upper_correction", {})
    uc_key = bucket_to_key.get(year_bucket)
    year_upper_corr = upper_corr_table.get(uc_key, 0) if uc_key else 0
    if year_upper_corr != 0:
        breakdown.append(("年式(上限)", year_upper_corr))
        upper += year_upper_corr

    # --- 年式幅 (上限から下げてレンジの広さを決める) ---
    width_table = params.get("year_range_width_below_upper", {})
    width_key = bucket_to_key.get(year_bucket)
    # 年式不明等でbucketが取れない場合は中堅相当のデフォルト幅
    if width_key and width_key in width_table:
        width = width_table[width_key]
    else:
        width = width_table.get("6〜10年 (中堅年式)", 7)

    high = upper
    low = high - width

    # クリップ
    high = max(0, min(100, high))
    low = max(0, min(100, low))

    return {
        "low": int(round(low)),
        "high": int(round(high)),
        "width": int(round(width)),
        "breakdown": breakdown,
        "is_sub_cat": is_sub_cat,
        "ok": True,
    }


def build_missing_items_advice(missing_items: list, brand_en: str = "") -> str:
    """欠品した付属品に応じて、Chosukeの観察促しメッセージを生成 (設計インサイト #002)。

    トーン原則: 「鍵紛失で大幅減額」(断定・答えを出す)はNG。
    「鍵単体の相場もあるから確認してみろ」(観察を促す)が正解。
    特に鍵・カデナ・ストラップ等、再取得可能だったり相場に影響する品目は厚く扱う。
    欠品が無ければ空文字を返す(カードを出さない)。
    """
    if not missing_items:
        return ""

    # 個別品目ごとの観察促し。
    # キーは欠品チェックリストの項目名(日本語)と一致させる必要があるため日本語のまま温存し、
    # 表示するセリフ本文だけ t() で言語切替する。
    item_tip_keys = {
        "鍵・カデナ": "msg.missing.keys",
        "ギャランティーカード": "msg.missing.gc",
        "箱": "msg.missing.box",
        "保存袋": "msg.missing.dustbag",
        "ストラップ": "msg.missing.strap",
        "取扱説明書(取説)": "msg.missing.manual",
    }

    parts = []
    matched = set()
    for item in missing_items:
        # 「その他: 〇〇」の自由記述はそのまま拾う
        if item.startswith("その他:"):
            parts.append(t("dyn.missing.other_freetext", item=item[4:].strip()))
            continue
        if item in item_tip_keys:
            parts.append(t(item_tip_keys[item]))
            matched.add(item)

    # チェックされたが個別tip未定義の品目はまとめて一言
    others = [i for i in missing_items if i not in matched and not i.startswith("その他:")]
    if others:
        parts.append(t("dyn.missing.others", items="・".join(others)))

    return " ".join(parts)


def _category_inspection_tip(cat: str) -> str:
    """カテゴリ別の『促す具体動作』を返す (設計インサイト #004)。
    時計・ジュエリーはルーペ必須、バッグはライト、等。
    キー(カテゴリ名)は inspect_cat と照合する内部キーなので日本語のまま温存し、
    表示する確認動作セリフだけ t() で言語切替する。"""
    tip_keys = {
        "時計": "msg.inspect.watch",
        "高級ジュエリー": "msg.inspect.fine_jewelry",
        "ジュエリー": "msg.inspect.jewelry",
        "ファッションジュエリー": "msg.inspect.fashion_jewelry",
        "バッグ": "msg.inspect.bag",
        "服": "msg.inspect.clothes",
        "靴": "msg.inspect.shoes",
        "SLG": "msg.inspect.slg",
        "ベルト": "msg.inspect.belt",
        "スカーフ": "msg.inspect.scarf",
        "メガネ・サングラス": "msg.inspect.glasses",
        "電子機器": "msg.inspect.electronics",
    }
    key = tip_keys.get(cat)
    return t(key) if key else t("msg.inspect.default")


def build_cost_thinking_text(brand_ja: str, calc: dict, rank: str, year_bucket: str,
                             inspect_cat: str = "") -> str:
    """Chosukeの『思考過程の独り言』を生成 (いかりや長介トーン)。

    設計インサイト #004: 答えを出さず観察を促す + 思考過程の言語化。
    前半=独り言で計算プロセスを見せる、後半=いかりや調で観察を促す。

    v0.10.1: 促し動作(ルーペ/ライト等)はこの関数から切り離し、独立した
    「確認動作カード」として常時表示するように変更。
    動的算出(Layer2)以外でも促し動作が出るようにするため。
    inspect_cat は後方互換のため引数だけ残してあるが、本文では未使用。
    """
    bd = calc["breakdown"]
    base_val = bd[0][1]

    parts = []
    parts.append(t("dyn.think.base", brand=brand_ja, base=base_val))

    # 各補正を独り言化。
    # label(日本語)は breakdown 由来の照合キーなので変更せず、部分一致で分岐する。
    # 表示セリフだけ t() 化。{val} には符号付き文字列(+3 / -7)を渡す。
    for label, val in bd[1:]:
        sval = f"{val:+d}"
        if "カテゴリ" in label:
            parts.append(t("dyn.think.subcat", label=label, val=sval))
        elif "Rank" in label:
            if val > 0:
                parts.append(t("dyn.think.rank_up", label=label, val=sval))
            else:
                parts.append(t("dyn.think.rank", label=label, val=sval))
        elif "ギャラ" in label:
            if val < 0:
                parts.append(t("dyn.think.gc_none", val=sval))
            else:
                parts.append(t("dyn.think.gc_has", val=sval))
        elif "付属品" in label:
            parts.append(t("dyn.think.accessories", val=sval))
        elif "定番" in label:
            parts.append(t("dyn.think.iconic", val=sval))
        elif "年式(上限)" in label:
            parts.append(t("dyn.think.year_ceiling", val=sval))

    # 年式幅の独り言 (v0.10.2: 年式が下限を広げていることを思考過程に見せる)
    # 年式は上限ではなく「上限からどれだけ下げて下限を取るか(=慎重に見る幅)」に効く。
    # これを独り言に出さないと「年式が反映されてない」ように見えるため明示する。
    width = calc.get("width", 0)
    if width:
        phrase_key = {
            "recent": "dyn.think.year_width.recent",
            "semi_new": "dyn.think.year_width.semi_new",
            "mid": "dyn.think.year_width.mid",
            "old": "dyn.think.year_width.old",
        }.get(year_bucket, "dyn.think.year_width.unknown")
        parts.append(t("dyn.think.year_width_line", phrase=t(phrase_key), width=width))

    parts.append(t("dyn.think.conclusion", low=calc["low"], high=calc["high"]))
    parts.append(t("msg.think.disclaimer"))

    return " ".join(parts)


# ============================================================
# Chosukeのエールメッセージ(原価率カードに添えて表示)
# ============================================================
CHOSUKE_CHEER_MESSAGE = (
    "お客様へ説明する話しはまとまってますか?"
    "価格に甘えない交渉を頑張りましょう!"
)


# ============================================================
# Chosukeの応答ロジック
# ============================================================
def chosuke_advise(brand_ja: str, brand_en: str, product_name: str, year: str,
                   accessories: str, screenshots_count: int,
                   rank: str = "未定",
                   price_min: float = 0, price_max: float = 0,
                   stamp_or_serial: str = "",
                   is_microchip: bool = False,
                   is_year_unknown: bool = False,
                   is_random_serial: bool = False,
                   gc_status: str = "na",
                   assess_cat: str = "",
                   accessories_status: str = "フルセット",
                   missing_items: list = None) -> dict:
    if missing_items is None:
        missing_items = []
    brands_df = load_brands()
    checklists_df = load_checklists()
    feedback_df = load_feedback()
    history_df = load_history()

    brand_row = brands_df[brands_df["brand_ja"] == brand_ja]
    if not brand_row.empty:
        cost_min = int(brand_row.iloc[0]["cost_ratio_min"])
        cost_max = int(brand_row.iloc[0]["cost_ratio_max"])
        category = brand_row.iloc[0]["category"]
        brand_notes = brand_row.iloc[0]["notes"]
    else:
        cost_min = None
        cost_max = None
        category = "不明"
        brand_notes = t("msg.brand_notes.unregistered")

    # ----- 促し動作カテゴリの確定 (v0.10.1: Layer判定とは独立) -----
    # ルーペ/ライト等の「確認動作」は原価率の算出方法(Layer)とは無関係に、
    # カテゴリさえ分かれば毎回出すべきもの。そのため Layer 判定より前に確定させる。
    # 判定優先順位:
    #   (1) マスタcategoryが電子機器 → "電子機器" 専用文(アクティベーションロック等)
    #       ※ "他の" へ正規化すると文房具等と混ざり的外れになるため最優先で拾う
    #   (2) 査定カテゴリ(絞り込み指定あり)
    #   (3) マスタcategoryを新表記へ正規化
    #   (4) いずれも取れなければ空 → デフォルトの確認動作
    if category == "電子機器":
        inspect_cat = "電子機器"
    elif assess_cat and assess_cat != "指定なし":
        inspect_cat = assess_cat
    elif category and category != "不明":
        inspect_cat = COST_CATEGORY_NORMALIZE.get(category, category)
    else:
        inspect_cat = ""  # カテゴリ不明 → デフォルトの確認動作にフォールバック
    inspection_tip = _category_inspection_tip(inspect_cat)

    # 欠品品目に応じた観察促し (v0.10.4: 設計インサイト #002)
    # 「一部欠品」で何が無いかを Chosuke が個別にコメントする。
    missing_advice = build_missing_items_advice(missing_items, brand_en)

    # ----- Layer 3: 過去の実査定実績ベースの推奨原価率 -----
    # 同ブランド+同品名の actual_cost_rate(レビュー済み)が3件以上あれば、
    # その中央値±2.5% で推奨値を上書き
    cost_source = "初期値"  # "初期値" or "実績"
    cost_actual_count = 0
    if (not history_df.empty
            and "actual_cost_rate" in history_df.columns
            and "product_name" in history_df.columns):
        actuals = history_df[
            (history_df["brand_ja"] == brand_ja) &
            (history_df["product_name"].astype(str).str.strip() == str(product_name).strip())
        ].copy()
        actuals["rate_num"] = pd.to_numeric(actuals.get("actual_cost_rate"), errors="coerce")
        actuals = actuals[actuals["rate_num"].notna() & (actuals["rate_num"] > 0)]
        if len(actuals) >= 3:
            median_rate = actuals["rate_num"].median()
            cost_min = max(0, int(round(median_rate - 2.5)))
            cost_max = min(100, int(round(median_rate + 2.5)))
            if cost_max - cost_min != 5:
                cost_max = cost_min + 5
            cost_source = "実績"
            cost_actual_count = len(actuals)

    # ----- Layer 2: 動的算出 (v0.10) -----
    # 実績ベース(Layer3)で上書きされていない場合のみ、
    # cost_params.json のパラメータでブランド×カテゴリ×Rank×ギャラ×付属品×年式から動的算出。
    # 設計インサイト #003 / #005 / #006
    cost_dynamic = None        # 算出結果 dict
    cost_thinking = ""         # 思考過程の独り言テキスト
    if cost_source != "実績":
        params = load_cost_params()
        if params:
            # 定番判定 (このあとの bubble 用と同じロジックを先取り)
            _iconic_str = ""
            if not brand_row.empty and "iconic_models" in brand_row.columns:
                _iconic_str = str(brand_row.iloc[0].get("iconic_models", "") or "")
            _is_iconic_pre = check_iconic_model(product_name, _iconic_str)
            # 年式バケット
            if is_microchip or is_year_unknown or is_random_serial:
                _bucket = ""  # 年式情報なし → デフォルト幅
            else:
                _bucket = get_year_bucket(year)
            # 主力カテゴリ (マスタの category)
            _master_cat = category if not brand_row.empty else "不明"
            # マスタ中央値 (override が無いブランドのフォールバック基準)
            _master_center = None
            if cost_min is not None and cost_max is not None:
                _master_center = (cost_min + cost_max) / 2.0
            cost_dynamic = compute_dynamic_cost_range(
                params=params,
                brand_en=brand_en,
                master_cat=_master_cat,
                assess_cat=assess_cat,
                rank=rank,
                gc_status=gc_status,
                accessories_status=accessories_status,
                is_iconic=_is_iconic_pre,
                year_bucket=_bucket,
                master_center=_master_center,
            )
            if cost_dynamic and cost_dynamic.get("ok"):
                cost_min = cost_dynamic["low"]
                cost_max = cost_dynamic["high"]
                cost_source = "動的算出"
                # 思考過程カードを生成 (促し動作は独立カード化したため inspect_cat は渡さない)
                cost_thinking = build_cost_thinking_text(
                    brand_ja, cost_dynamic, rank, _bucket
                )

    relevant_checks = checklists_df[checklists_df["brand_ja"] == brand_ja]

    # フィードバック(正式化済み)
    if "promoted" in feedback_df.columns and not feedback_df.empty:
        feedback_df = feedback_df.copy()
        feedback_df["promoted_bool"] = feedback_df["promoted"].astype(str).str.lower().isin(["true", "1"])
        relevant_feedback = feedback_df[
            (feedback_df["brand_ja"] == brand_ja) & (feedback_df["promoted_bool"] == True)
        ]
    else:
        relevant_feedback = pd.DataFrame()

    # 吹き出しメッセージ (v0.10: いかりや長介トーンに統一 - 設計インサイト #004)
    bubble_parts = []
    bubble_parts.append(t("dyn.bubble.intro", brand=brand_ja, brand_en=brand_en, product=product_name))

    # 定番モデル反応 (v0.9)
    iconic_str = ""
    if not brand_row.empty and "iconic_models" in brand_row.columns:
        iconic_str = str(brand_row.iloc[0].get("iconic_models", "") or "")
    is_iconic = check_iconic_model(product_name, iconic_str)
    if is_iconic:
        bubble_parts.append(tr("iconic_match"))

    if screenshots_count > 0:
        bubble_parts.append(t("dyn.bubble.screenshots_ok", n=screenshots_count))
    else:
        bubble_parts.append(t("msg.bubble.screenshots_none"))

    range_info = None
    if price_min > 0 and price_max > 0:
        range_info = market_range_check(price_min, price_max)
        bubble_parts.append(t("dyn.bubble.market_memo", pmin=f"{price_min:.0f}", pmax=f"{price_max:.0f}"))
        bubble_parts.append(range_info["message"])

    if rank and rank != "未定":
        bubble_parts.append(t("dyn.bubble.rank_tentative", rank=rank))
    else:
        bubble_parts.append(t("msg.bubble.rank_undecided"))

    if cost_min is not None:
        if cost_source == "実績":
            bubble_parts.append(t("dyn.bubble.cost_actual", n=cost_actual_count, cmin=cost_min, cmax=cost_max))
        elif cost_source == "動的算出":
            bubble_parts.append(t("msg.bubble.cost_dynamic"))
        else:
            bubble_parts.append(t("dyn.bubble.cost_initial", cmin=cost_min, cmax=cost_max))
    else:
        bubble_parts.append(t("msg.bubble.not_registered_close"))

    bubble_msg = " ".join(bubble_parts)

    # 年式判定 (v0.9: tr()経由 + 年式バケット反応を追加)
    year_advice = ""
    year_tag_msg = ""  # 年式タグ反応 (いかりや長介トーン)

    if is_microchip:
        year_advice = tr("year_microchip")
    elif is_year_unknown:
        year_advice = tr("year_unknown")
    elif is_random_serial:
        year_advice = tr("year_random_serial")
    elif stamp_or_serial:
        if brand_en == "HERMES":
            year_advice = hermes_year_from_stamp(stamp_or_serial)
        elif brand_en == "CHANEL":
            year_advice = chanel_year_from_serial(stamp_or_serial)
        elif brand_en == "ROLEX":
            year_advice = rolex_year_from_serial(stamp_or_serial)

    # v0.9: 年式タグ反応 (バケット別の合いの手)
    # year欄に4桁数字が入っていれば、年代を判定して反応
    # マイクロチップ/年式不明/ランダムシリアル扱いの時は表示しない (専用メッセージと競合するため)
    if not is_microchip and not is_year_unknown and not is_random_serial:
        bucket = get_year_bucket(year)
        if bucket == "recent":
            year_tag_msg = tr("year_recent")
        elif bucket == "semi_new":
            year_tag_msg = tr("year_semi_new")
        elif bucket == "mid":
            year_tag_msg = tr("year_mid")
        elif bucket == "old":
            year_tag_msg = tr("year_old")

    # 過去履歴の比較
    history_msg = ""
    if not history_df.empty and "product_name" in history_df.columns:
        past = history_df[
            (history_df["brand_ja"] == brand_ja) &
            (history_df["product_name"].astype(str).str.strip() == str(product_name).strip())
        ].copy()
        if not past.empty:
            past["pmin"] = pd.to_numeric(past.get("price_min_usd"), errors="coerce")
            past["pmax"] = pd.to_numeric(past.get("price_max_usd"), errors="coerce")
            past = past[(past["pmin"] > 0) & (past["pmax"] > 0)]

            if not past.empty:
                avg_min = past["pmin"].mean()
                avg_max = past["pmax"].mean()
                count = len(past)
                history_msg = t("dyn.bubble.history", brand=brand_ja, product=product_name,
                                amin=f"{avg_min:.0f}", amax=f"{avg_max:.0f}", n=count)
                if price_min > 0 and price_max > 0:
                    if abs(price_max - avg_max) > avg_max * 0.15 or abs(price_min - avg_min) > avg_min * 0.15:
                        history_msg += t("dyn.bubble.history_deviation",
                                         pmin=f"{price_min:.0f}", pmax=f"{price_max:.0f}")

    return {
        "bubble_msg": bubble_msg,
        "cost_min": cost_min,
        "cost_max": cost_max,
        "cost_source": cost_source,
        "cost_actual_count": cost_actual_count,
        "cost_thinking": cost_thinking,
        "cost_dynamic": cost_dynamic,
        "inspection_tip": inspection_tip,
        "inspect_cat": inspect_cat,
        "missing_advice": missing_advice,
        "category": category,
        "brand_notes": brand_notes,
        "checklists": relevant_checks,
        "past_feedback": relevant_feedback,
        "rank": rank,
        "year_advice": year_advice,
        "year_tag_msg": year_tag_msg,
        "is_iconic": is_iconic,
        "history_msg": history_msg,
        "range_info": range_info,
    }


# ============================================================
# UI: スタイル
# ============================================================
def inject_css():
    st.markdown("""
    <style>
    .stApp { background: #f7f5f1; }

    .chosuke-header {
        background: white;
        border-bottom: 1px solid #e5e0d7;
        padding: 16px 24px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .chosuke-icon {
        width: 56px; height: 56px;
        background: linear-gradient(135deg, #d4a574 0%, #8b6f47 100%);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 28px;
        box-shadow: 0 2px 8px rgba(139, 111, 71, 0.25);
    }
    .chosuke-title {
        font-family: Georgia, serif;
        font-size: 22px; font-weight: 600;
        color: #2b2520; margin: 0;
    }
    .chosuke-tagline {
        font-style: italic; color: #8b6f47; font-size: 13px;
    }
    .chosuke-subtitle {
        font-size: 11px; color: #9a9088;
        text-transform: uppercase; letter-spacing: 0.08em;
    }

    .chosuke-bubble {
        background: linear-gradient(180deg, #fdf9f2 0%, #faf3e6 100%);
        border: 1px solid #d4ccc0;
        border-radius: 10px;
        padding: 18px 20px;
        margin: 16px 0;
    }
    .chosuke-name {
        font-family: Georgia, serif;
        font-weight: 600; font-size: 14px;
        color: #8b6f47; margin-bottom: 8px;
    }
    .chosuke-text {
        color: #2b2520; font-size: 14px; line-height: 1.7;
    }

    .cost-ratio-card {
        background: linear-gradient(135deg, #2b2520 0%, #3d342c 100%);
        color: #f7f5f1;
        padding: 18px 20px;
        border-radius: 10px;
        margin: 12px 0;
    }
    .cost-ratio-label {
        font-size: 11px; text-transform: uppercase;
        letter-spacing: 0.12em; color: rgba(247,245,241,0.6);
    }
    .cost-ratio-value {
        font-family: Georgia, serif;
        font-size: 38px; font-weight: 700;
        color: #d4a574; line-height: 1.1;
    }
    .cost-ratio-note {
        font-size: 11px; color: rgba(247,245,241,0.5);
        font-style: italic;
    }
    .cost-ratio-cheer {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid rgba(212, 165, 116, 0.3);
        font-size: 13px;
        color: #d4a574;
        line-height: 1.6;
    }

    .thinking-card {
        background: #f4f0e8;
        border: 1px dashed #b89968;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 12px 0;
    }
    .thinking-label {
        font-size: 12px;
        font-weight: 700;
        color: #8b6f47;
        margin-bottom: 8px;
        letter-spacing: 0.03em;
    }
    .thinking-text {
        font-size: 14px;
        color: #3d342c;
        line-height: 1.85;
    }
    .thinking-text b {
        color: #a8742c;
        font-weight: 700;
    }

    .inspection-card {
        background: #f0ede4;
        border-left: 4px solid #8b6f47;
        padding: 13px 18px;
        border-radius: 6px;
        margin: 12px 0;
    }
    .inspection-label {
        font-size: 13px;
        font-weight: 700;
        color: #6e5836;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }
    .inspection-text {
        font-size: 14px;
        color: #3d342c;
        line-height: 1.7;
    }

    .missing-card {
        background: #fbf0e6;
        border-left: 4px solid #c98a4b;
        padding: 13px 18px;
        border-radius: 6px;
        margin: 12px 0;
    }
    .missing-label {
        font-size: 13px;
        font-weight: 700;
        color: #9a5e23;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }
    .missing-text {
        font-size: 14px;
        color: #3d342c;
        line-height: 1.75;
    }
    .missing-text b {
        color: #b45309;
        font-weight: 700;
    }

    .year-card {
        background: #fff8e7;
        border-left: 4px solid #d4a574;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 12px 0;
    }
    .year-tag-card {
        background: linear-gradient(135deg, #fdf9f2 0%, #faf0dc 100%);
        border-left: 4px solid #8b6f47;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 12px 0;
        line-height: 1.7;
    }
    .history-card {
        background: #eef4ee;
        border-left: 4px solid #6b8e6b;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 12px 0;
    }
    .range-card-narrow { background: #eef4ee; border-left: 4px solid #6b8e6b; padding: 12px 16px; border-radius: 6px; margin: 12px 0; }
    .range-card-normal { background: #fdf9f2; border-left: 4px solid #d4a574; padding: 12px 16px; border-radius: 6px; margin: 12px 0; }
    .range-card-wide { background: #fef0e8; border-left: 4px solid #c97a4d; padding: 12px 16px; border-radius: 6px; margin: 12px 0; }
    .range-card-very_wide { background: #fde4e4; border-left: 4px solid #b04444; padding: 12px 16px; border-radius: 6px; margin: 12px 0; }

    h2, h3 { color: #2b2520; }

    .chosuke-footer {
        text-align: center; padding: 24px;
        font-size: 11px; color: #9a9088;
        letter-spacing: 0.04em; margin-top: 32px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Streamlit の "C" キー単体ショートカット(Clear caches)を無効化する ---
    # 商品名コピー(ドラッグ選択中など)で C が拾われ、毎回 Clear caches ダイアログが
    # 出てしまう問題への対処。Ctrl+C / Cmd+C(本物のコピー)は一切妨げない。
    import streamlit.components.v1 as _components
    _components.html(
        """
        <script>
        const doc = window.parent.document;
        if (!doc._chosukeKeyGuard) {
            doc._chosukeKeyGuard = true;
            doc.addEventListener("keydown", function (e) {
                // 修飾キー付き(Ctrl/Cmd/Alt)は本物のショートカットなので通す
                if (e.ctrlKey || e.metaKey || e.altKey) return;
                // 入力欄にフォーカスがあるときは何もしない
                const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : "";
                if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;
                // 修飾キーなしの C / R(Clear caches / Rerun)を握りつぶす
                const k = (e.key || "").toLowerCase();
                if (k === "c" || k === "r") {
                    e.stopPropagation();
                    e.preventDefault();
                }
            }, true);
        }
        </script>
        """,
        height=0,
    )


def render_header():
    st.markdown("""
    <div class="chosuke-header">
        <div class="chosuke-icon">🦉</div>
        <div>
            <div class="chosuke-title">Chosuke</div>
            <div class="chosuke-tagline">Wise eyes never miss a corner.</div>
            <div class="chosuke-subtitle">AI Appraisal Assistant · Eco Ring Cambodia</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 画面1: 査定モード
# ============================================================
def _appr_nonce() -> int:
    """査定入力ウィジェットの世代番号(nonce)。クリアのたびに +1 する。"""
    if "apprai_nonce" not in st.session_state:
        st.session_state["apprai_nonce"] = 0
    return st.session_state["apprai_nonce"]


def _k(base: str) -> str:
    """nonce 付きウィジェットキーを作る。例: _k("product") -> "apprai_product_0"

    v0.10.9: クリアが実ブラウザで効かない問題への根本対処(nonce方式)。
    これまでの session_state.pop 方式は、pop してもブラウザから送られてくる
    前回値が同じ再描画内でウィジェットに再結合され、入力欄だけ残る現象が出た
    (右の応答は消えるのに左の入力は残る、という症状で確定)。
    そこで各入力欄の key 末尾に世代番号を付け、クリア時に番号を +1 することで
    Streamlit に「別の新しいウィジェット」と認識させ、確実に初期状態で出す。
    ※担当staff(apprai_staff)は nonce を付けず固定キーのまま=クリアしても残す。
    """
    return f"apprai_{base}_{_appr_nonce()}"


def _apply_appraisal_clear_if_requested():
    """クリア要求フラグが立っていたら、ウィジェット生成より前にクリアを適用する。

    nonce方式: 世代番号を +1 するだけで全入力欄が新規ウィジェット化され初期化される。
    応答(advice_*)も初期化する。担当staff(固定キー)は触らないので残る。
    """
    if not st.session_state.get("_clear_requested", False):
        return

    # 世代番号を進める → 次に生成される入力欄は全て新規キーになり初期値で出る
    st.session_state["apprai_nonce"] = st.session_state.get("apprai_nonce", 0) + 1

    # 念のため、古い世代のチェックボックス類の残骸も掃除(メモリ蓄積防止)
    for k in list(st.session_state.keys()):
        if k.startswith("acc_main_") or k.startswith("acc_extra_") or k.startswith("chk_"):
            st.session_state.pop(k, None)

    # Chosukeの応答もクリア
    st.session_state.advice_result = None
    st.session_state.advice_meta = {}

    # フラグを下ろす
    st.session_state["_clear_requested"] = False


def _request_appraisal_clear():
    """クリア/リセットボタンの on_click。フラグを立てるだけ。

    実際のクリアは次の再描画冒頭で _apply_appraisal_clear_if_requested() が行う。
    """
    st.session_state["_clear_requested"] = True


def _request_appraisal_clear():
    """クリア/リセットボタンの on_click。フラグを立てるだけ。

    実際のクリアは次の再描画冒頭で _apply_appraisal_clear_if_requested() が行う。
    """
    st.session_state["_clear_requested"] = True


def appraisal_mode():
    # v0.10.8: クリア要求があれば、ウィジェット生成より前にここで適用する。
    #   (フラグ方式。コールバックの発火タイミングに依存せず確実にクリアするため)
    _apply_appraisal_clear_if_requested()

    # 見出し行に上部クリアボタンを併設(見出しの右端)
    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown("## 🔍 " + t("ui.mode.appraisal"))
    with head_r:
        st.write("")  # 縦位置をタイトルにそろえる微調整
        st.button(t("ui.btn.clear"), key="apprai_clear_top", use_container_width=True,
                  help=t("ui.btn.clear.help"),
                  on_click=_request_appraisal_clear)
    st.caption(t("ui.appraisal.caption"))

    if "advice_result" not in st.session_state:
        st.session_state.advice_result = None
    if "advice_meta" not in st.session_state:
        st.session_state.advice_meta = {}

    col_input, col_output = st.columns([1, 1.3], gap="large")

    # ----- 左: 商品情報入力 -----
    with col_input:
        # ===== 担当staff(最上部・必須項目) =====
        # v0.12.4: フリーテキスト入力(text_input)による表記ゆれ(Komatsu/komastu/komatu…)を
        #   防ぐため、staff_master.csv からの選択式(selectbox)に変更。
        #   「(➕ 新規staffを追加)」を選んだときだけ入力欄を出し、確定した名前はマスタへ自動登録する。
        #   ※固定キー apprai_staff の意味は「最終的に確定したstaff名」を保持する点で従来どおり。
        #     クリア時に残す挙動(_clear_appraisal_inputs が触らない)も維持される。
        st.markdown("### " + t("ui.staff.header"))

        _STAFF_NEW_OPTION = "(➕ 新規staffを追加)"
        staff_options = load_staff_master()
        # クラウド版: 表記ゆれ再発防止のため、新規staff追加は管理者のみ。
        # staff ロールでは選択肢に「新規追加」を出さない(選ぶだけ)。
        _is_admin = st.session_state.get("role") == "admin"
        if _is_admin:
            staff_select_options = staff_options + [_STAFF_NEW_OPTION]
        else:
            staff_select_options = staff_options

        # 既に確定済みのstaff(apprai_staff)があれば、それを初期選択にする。
        _current_staff = str(st.session_state.get("apprai_staff", "") or "").strip()
        if _current_staff and _current_staff in staff_options:
            _staff_index = staff_options.index(_current_staff)
        else:
            _staff_index = None

        _staff_choice = st.selectbox(
            t("ui.staff.header"),
            staff_select_options,
            index=_staff_index,
            placeholder=t("ui.staff.placeholder"),
            key="apprai_staff_select",
            label_visibility="collapsed",
            help=t("ui.staff.help")
        )

        if _is_admin and _staff_choice == _STAFF_NEW_OPTION:
            _staff_new = st.text_input(
                "新しいstaff名",
                key="apprai_staff_new",
                placeholder=t("ui.settings.staff_placeholder"),
                help=t("ui.staff.add_help")
            ).strip()
            staff = _staff_new
            if _staff_new:
                # 新規入力された名前をマスタに登録(次回以降は選択肢に出る)
                add_staff_to_master(_staff_new)
        elif _staff_choice:
            staff = _staff_choice
        else:
            staff = ""

        # 確定したstaff名を固定キーに反映(履歴保存・クリア後の保持はこのキーを使う)
        st.session_state["apprai_staff"] = staff

        if not staff.strip():
            st.caption("⚠️ " + t("ui.staff.required"))

        st.markdown("### " + t("ui.product.header"))

        brands_df = load_brands()
        brands_df_sorted = brands_df.sort_values("brand_ja").reset_index(drop=True)

        # まずカテゴリを「内部状態」として保持(UIは後で出す)
        # ※ブランド絞り込みに使うため、現在の選択値を先読みする。
        #   v0.10.9: nonce方式に伴い、カテゴリの現在値も nonce 付きキーから読む。
        #   クリア直後は nonce が変わって該当キーが無い → 「指定なし」になる。
        selected_category = st.session_state.get(_k("category"), "指定なし")

        # カテゴリでブランドを絞り込み(現在の選択値を使う)
        # v0.10.6: 絞り込み結果が0件になったら自動で全ブランド表示に戻す(フォールバック)。
        #   ハイブランドは1ブランドで多カテゴリ(バッグ/財布/スカーフ/時計…)を扱うのが実態。
        #   マスタの category は1ブランド1値しか持てないため、スカーフ・アクセサリー等を選ぶと
        #   ヴィトン等の主要ブランドが候補から消える取りこぼしが起きていた(査定不能になる)。
        #   → ブランドを消さないことを最優先にし、該当0件なら絞り込みを無効化する。
        if selected_category != "指定なし":
            def _matches_category(master_cat: str) -> bool:
                normalized = BRAND_CATEGORY_NORMALIZE.get(master_cat, master_cat)
                return normalized == selected_category

            candidate_df = brands_df_sorted[
                brands_df_sorted["category"].apply(_matches_category)
            ].reset_index(drop=True)

            if len(candidate_df) > 0:
                filtered_df = candidate_df
            else:
                # 該当ブランドが1件も無い → 絞り込みを諦めて全ブランド表示に戻す
                filtered_df = brands_df_sorted
        else:
            filtered_df = brands_df_sorted

        brand_labels = [
            f"{row['brand_ja']}  /  {row['brand_en']}"
            for _, row in filtered_df.iterrows()
        ] + ["(その他/未登録)"]

        # v0.10.7: フォールバック時の案内文は削除(現場フィードバック: 不要・くどい)。
        #   ブランドが消えない挙動(フォールバック)はそのまま維持。
        #   絞り込めない場合は黙って全ブランドを出すのが自然な体験。

        # ブランド選択(カテゴリより上に表示)
        sel_label = st.selectbox(
            t("ui.brand.label"),
            brand_labels,
            index=None,
            placeholder=t("ui.brand.placeholder"),
            key=_k("brand_label")
        )

        # カテゴリ選択(ブランドの下・絞り込みフィルタ)
        # ※key="apprai_category" は session_state で復元されるので index 指定不要
        selected_category = st.selectbox(
            t("ui.category.label"),
            CATEGORY_OPTIONS,
            format_func=_category_display,
            key=_k("category"),
            help=t("ui.category.help")
        )

        if sel_label is None:
            brand_ja = ""
            brand_en = ""
        elif sel_label == "(その他/未登録)":
            brand_ja = st.text_input(t("ui.brand.name_ja"), key=_k("brand_custom_ja"))
            brand_en = st.text_input(t("ui.brand.name_en"), key=_k("brand_custom_en"))
        else:
            parts = sel_label.split("  /  ")
            brand_ja = parts[0]
            brand_en = parts[1] if len(parts) > 1 else ""

        product_name = st.text_input(t("ui.product.label"), value="", placeholder=t("ui.product.placeholder"), key=_k("product"))

        col_y, col_r = st.columns([1, 1])
        with col_y:
            year = st.text_input(t("ui.year.label"), placeholder=t("ui.year.placeholder"), key=_k("year"))
        with col_r:
            rank = st.selectbox(t("ui.rank.label"), RANK_OPTIONS, format_func=_rank_display, key=_k("rank"))

        # 付属品は単独行(直下に「一部欠品」の詳細チェックリストを出すため)
        # ※ option の値("フルセット"等)は履歴保存・判定ロジックで使う固定キーなので翻訳しない。
        #   表示だけ format_func で言語切替する。
        _ACC_LABEL = {
            "フルセット": "ui.acc.full",
            "一部欠品": "ui.acc.partial",
            "本体のみ": "ui.acc.bodyonly",
        }
        accessories_status = st.selectbox(
            t("ui.acc.label"),
            ["フルセット", "一部欠品", "本体のみ"],
            format_func=lambda v: t(_ACC_LABEL.get(v, v)),
            key=_k("acc_status")
        )

        # 「一部欠品」のときだけ詳細チェックリストを表示
        # (付属品プルダウンの直下に置くことで、選択→入力の視線が途切れないようにする)
        accessories_detail = ""
        missing_items = []  # 欠品品目(一部欠品以外では空のまま → Chosukeの欠品コメントも出ない)
        if accessories_status == "一部欠品":
            with st.container(border=True):
                st.caption(t("ui.acc.missing_prompt"))

                # 主要項目(常に表示)
                main_items = ["箱", "保存袋", "ギャランティーカード",
                              "取扱説明書(取説)", "鍵・カデナ", "ストラップ"]
                main_cols = st.columns(2)
                for i, item in enumerate(main_items):
                    with main_cols[i % 2]:
                        if st.checkbox(item, key=_k(f"acc_main_{item}")):
                            missing_items.append(item)

                # 「もっと見る」展開
                with st.expander(t("ui.more_fields")):
                    extra_items = ["内箱", "外箱", "化粧箱", "レシート・購入証明",
                                   "シリアルカード", "ショッピングバッグ(紙袋)",
                                   "予備コマ", "タグ"]
                    extra_cols = st.columns(2)
                    for i, item in enumerate(extra_items):
                        with extra_cols[i % 2]:
                            if st.checkbox(item, key=_k(f"acc_extra_{item}")):
                                missing_items.append(item)

                    other_text = st.text_input(
                        "その他(自由記述)",
                        placeholder=t("ui.acc.other_placeholder"),
                        key=_k("acc_other")
                    )
                    if other_text.strip():
                        missing_items.append(f"その他: {other_text.strip()}")

                accessories_detail = ", ".join(missing_items) if missing_items else "(欠品項目未指定)"

        # ギャランティーカード有無 (v0.10: 推奨原価率の動的算出に使用)
        # ※ option値は下の gc_status マップのキーなので翻訳しない。表示のみ format_func で切替。
        _GC_LABEL = {
            "対象外 / 不問": "ui.gc.na",
            "有り": "ui.gc.has",
            "無し": "ui.gc.none",
        }
        gc_choice = st.radio(
            t("ui.gc.label"),
            ["対象外 / 不問", "有り", "無し"],
            format_func=lambda v: t(_GC_LABEL.get(v, v)),
            horizontal=True,
            key=_k("gc"),
            help=t("ui.gc.help")
        )
        gc_status = {"有り": "has", "無し": "none", "対象外 / 不問": "na"}[gc_choice]

        # 製造年の補助フラグ: マイクロチップ品 / 年式不明 / ランダムシリアル品
        col_chip, col_unknown, col_random = st.columns(3)
        with col_chip:
            is_microchip = st.checkbox(
                t("ui.flag.microchip"),
                key=_k("microchip"),
                help=t("ui.microchip.help")
            )
        with col_unknown:
            is_year_unknown = st.checkbox(
                t("ui.flag.year_unknown"),
                key=_k("year_unknown"),
                help=t("ui.year_unknown.help")
            )
        with col_random:
            is_random_serial = st.checkbox(
                t("ui.flag.random_serial"),
                key=_k("random_serial"),
                help=t("ui.random_serial.help")
            )

        # 履歴・応答ロジック用に付属品情報を文字列化
        if accessories_status == "フルセット":
            accessories = "フルセット"
        elif accessories_status == "本体のみ":
            accessories = "本体のみ"
        else:  # 一部欠品
            accessories = f"一部欠品 [{accessories_detail}]" if accessories_detail else "一部欠品"

        # ブランド固有: 刻印・シリアル入力
        stamp_or_serial = ""
        if brand_en in ("HERMES", "CHANEL", "ROLEX"):
            label_map = {
                "HERMES": "刻印(例: A, ○A, □R, R など)",
                "CHANEL": "シリアル番号(7桁または8桁)",
                "ROLEX": "シリアル番号(数字または英数字)",
            }
            stamp_or_serial = st.text_input(
                label_map[brand_en],
                placeholder=t("ui.serial.placeholder"),
                key=_k("stamp")
            )

        st.markdown("### " + t("ui.market.header"))
        st.caption(t("ui.market.caption"))
        col_pmin, col_pmax = st.columns(2)
        with col_pmin:
            price_min = st.number_input(t("ui.market.min"), min_value=0, step=1, format="%d", key=_k("pmin"))
        with col_pmax:
            price_max = st.number_input(t("ui.market.max"), min_value=0, step=1, format="%d", key=_k("pmax"))

        st.markdown("### " + t("ui.screenshot.header"))
        st.caption(t("ui.screenshot.caption"))
        uploaded_files = st.file_uploader(
            "スクショをドラッグ&ドロップ",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=_k("screenshots")
        )

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            staff_filled = bool(staff.strip())
            brand_filled = bool(brand_ja and brand_ja.strip())
            ready = staff_filled and brand_filled
            if not staff_filled:
                btn_help = t("ui.staff.need")
            elif not brand_filled:
                btn_help = t("ui.brand.need")
            else:
                btn_help = None
            ask_chosuke = st.button(
                t("ui.btn.consult"),
                type="primary",
                use_container_width=True,
                disabled=not ready,
                help=btn_help
            )
        with col_btn2:
            # v0.10.7: 上部クリアと同様 on_click 方式に統一(確実にクリアを効かせる)
            st.button(t("ui.btn.reset"), use_container_width=True,
                      help=t("ui.btn.clear.help"),
                      on_click=_request_appraisal_clear)

    # ----- ボタン押下処理 -----
    if ask_chosuke and brand_ja and product_name and staff.strip():
        _ts_iso = datetime.now().isoformat(timespec="seconds")
        screenshots_count = 0
        if uploaded_files:
            screenshots_count = len(uploaded_files)
            # shot_id は査定のtimestampを使う(一意)。各画像を縮小してスプレッドシートに保存。
            for i, f in enumerate(uploaded_files):
                try:
                    be.save_screenshot(_ts_iso, i, f.read())
                except Exception as e:
                    st.warning(f"スクショの保存に失敗しました({f.name}): {e}")

        advice = chosuke_advise(
            brand_ja, brand_en, product_name, year, accessories,
            screenshots_count, rank,
            price_min, price_max, stamp_or_serial,
            is_microchip, is_year_unknown,
            is_random_serial=is_random_serial,
            gc_status=gc_status,
            assess_cat=(selected_category if selected_category != "指定なし" else ""),
            accessories_status=accessories_status,
            missing_items=missing_items,
        )

        append_history({
            "timestamp": _ts_iso,
            "staff": staff,
            "brand_ja": brand_ja,
            "brand_en": brand_en,
            "category": selected_category if selected_category != "指定なし" else "",
            "product_name": product_name,
            "year": year,
            "is_microchip": "Y" if is_microchip else "",
            "is_year_unknown": "Y" if is_year_unknown else "",
            "is_random_serial": "Y" if is_random_serial else "",
            "accessories": accessories,
            "rank": rank,
            "gc_status": gc_status,
            "price_min_usd": price_min if price_min > 0 else "",
            "price_max_usd": price_max if price_max > 0 else "",
            "screenshots_count": screenshots_count,
            "notes": "",
            "actual_cost_rate": "",
            "yuhei_comment": "",
            "review_status": "pending",
            "reviewed_at": "",
            "tags": "",
            # スクショは screenshots タブに timestamp(_ts_iso)で紐付けて保存済み。
            "screenshot_ids": _ts_iso if screenshots_count > 0 else "",
        })

        st.session_state.advice_result = advice
        st.session_state.advice_meta = {
            "brand_ja": brand_ja, "brand_en": brand_en,
            "product_name": product_name, "staff": staff,
        }

    # ----- 右: Chosukeの応答 -----
    with col_output:
        st.markdown("### " + t("ui.response.header"))

        if st.session_state.advice_result is None:
            if ask_chosuke:
                st.warning(t("ui.need_brand_product"))
            else:
                st.info(t("ui.response.empty"))
        else:
            advice = st.session_state.advice_result
            meta = st.session_state.advice_meta

            st.markdown(f"""
            <div class="chosuke-bubble">
                <div class="chosuke-name">🦉 Chosuke</div>
                <div class="chosuke-text">{advice["bubble_msg"]}</div>
            </div>
            """, unsafe_allow_html=True)

            if advice.get("range_info"):
                ri = advice["range_info"]
                level = ri["level"]
                if level != "unknown":
                    st.markdown(f"""
                    <div class="range-card-{level}">
                        <strong>{t("ui.card.range_header")}</strong><br>
                        {ri["message"]}
                    </div>
                    """, unsafe_allow_html=True)

            if advice["cost_min"] is not None:
                _src = advice.get("cost_source")
                if _src == "実績":
                    source_label = t("dyn.card.cost_src_actual", n=advice.get('cost_actual_count', 0))
                elif _src == "動的算出":
                    source_label = t("ui.card.cost_src_dynamic")
                else:
                    source_label = t("ui.card.cost_src_initial")
                st.markdown(f"""
                <div class="cost-ratio-card">
                    <div class="cost-ratio-label">{t("ui.card.cost_label", src=source_label)}</div>
                    <div class="cost-ratio-value">{advice["cost_min"]}% 〜 {advice["cost_max"]}%</div>
                    <div class="cost-ratio-note">{t("ui.card.cost_note")}</div>
                    <div class="cost-ratio-cheer">🦉 {t("msg.negotiation_prompt")}</div>
                </div>
                """, unsafe_allow_html=True)

                # v0.10: 思考過程カード (動的算出時のみ)
                # 設計インサイト #004: 数字だけでなく「どう考えたか」を見せる
                if advice.get("cost_thinking"):
                    st.markdown(f"""
                    <div class="thinking-card">
                        <div class="thinking-label">{t("ui.card.thinking_label")}</div>
                        <div class="thinking-text">{advice["cost_thinking"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # v0.10.1: 確認動作カード (Layerに関係なく常時表示)
            # 設計インサイト #004: 鑑定士の手を止めさせ、具体動作(ルーペ/ライト等)を促す。
            # 原価率の算出方法(実績/動的/初期値)に関わらず、カテゴリが分かれば必ず出す。
            if advice.get("inspection_tip"):
                _ins_cat = advice.get("inspect_cat") or t("ui.card.inspect_default_cat")
                st.markdown(f"""
                <div class="inspection-card">
                    <div class="inspection-label">{t("dyn.card.inspection_label", cat=_ins_cat)}</div>
                    <div class="inspection-text">{advice["inspection_tip"]}</div>
                </div>
                """, unsafe_allow_html=True)

            # v0.10.4: 欠品アドバイスカード (一部欠品で品目チェックがあるときだけ)
            # 設計インサイト #002: 欠品を断定減額せず、観察を促す。
            if advice.get("missing_advice"):
                st.markdown(f"""
                <div class="missing-card">
                    <div class="missing-label">📦 付属品の欠品について</div>
                    <div class="missing-text">{advice["missing_advice"]}</div>
                </div>
                """, unsafe_allow_html=True)

            if advice.get("year_advice"):
                st.markdown(f"""
                <div class="year-card">
                    <strong>{t("ui.card.year_label")}</strong><br>
                    {advice["year_advice"]}
                </div>
                """, unsafe_allow_html=True)

            # v0.9: 年式タグ反応 (いかりや長介トーン)
            if advice.get("year_tag_msg"):
                st.markdown(f"""
                <div class="year-tag-card">
                    <strong>🦉 Chosukeより一言</strong><br>
                    {advice["year_tag_msg"]}
                </div>
                """, unsafe_allow_html=True)

            if advice.get("history_msg"):
                st.markdown(f"""
                <div class="history-card">
                    <strong>{t("ui.card.history_label")}</strong><br>
                    {advice["history_msg"]}
                </div>
                """, unsafe_allow_html=True)

            # 注意点(統合表示)
            notes_items = []
            if advice["brand_notes"]:
                notes_items.append({"src": t("ui.card.notes_src_initial"), "content": td(advice["brand_notes"], st.session_state.lang)})
            if not advice["past_feedback"].empty:
                for _, row in advice["past_feedback"].iterrows():
                    notes_items.append({
                        "src": t("ui.card.notes_src_feedback", type=row.get('feedback_type','')),
                        "content": row["content"]
                    })

            if notes_items:
                st.markdown("#### " + t("ui.card.brand_notes"))
                for item in notes_items:
                    with st.container(border=True):
                        st.markdown(f"_{item['src']}_")
                        st.markdown(item["content"])

            # チェック項目
            # 「相場根拠は充分か?」を全カテゴリ共通の先頭固定項目として表示
            st.markdown("#### " + t("ui.card.checklist"))
            with st.container(border=True):
                st.checkbox(
                    f"**{t('ui.checklist.baseline_item')}**",
                    key=f"chk_baseline_{meta.get('brand_ja','')}_{meta.get('product_name','')}"
                )
                st.caption(t("ui.checklist.baseline_hint"))

            # ブランド固有のチェックリスト
            if not advice["checklists"].empty:
                for idx, row in advice["checklists"].iterrows():
                    chk_key = f"chk_{meta.get('brand_ja','')}_{idx}_{row['check_item']}"
                    with st.container(border=True):
                        st.checkbox(f"**{td(row['check_item'], st.session_state.lang)}**", key=chk_key)
                        st.caption(td(row["hint"], st.session_state.lang))

            # フィードバック欄
            st.markdown("---")
            st.markdown("#### " + t("ui.card.feedback"))
            st.caption(t("ui.feedback.caption"))

            with st.form("feedback_form"):
                # selectbox の値(日本語)は feedback_type として保存・照合されるので温存し、
                # 表示だけ format_func で言語切替する。
                _FB_TYPE_LABEL = {
                    "不足してた確認事項": "ui.feedback.type.missing",
                    "相場感のズレ": "ui.feedback.type.market",
                    "ノウハウ追加": "ui.feedback.type.knowhow",
                    "その他": "ui.feedback.type.other",
                }
                fb_type = st.selectbox(
                    t("ui.feedback.type_label"),
                    ["不足してた確認事項", "相場感のズレ", "ノウハウ追加", "その他"],
                    format_func=lambda v: t(_FB_TYPE_LABEL.get(v, v))
                )
                fb_content = st.text_area(t("ui.feedback.content_label"), placeholder=t("ui.feedback.content_placeholder"))
                fb_submit = st.form_submit_button(t("ui.feedback.submit"))

                if fb_submit and fb_content:
                    append_feedback({
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "staff": meta.get("staff", ""),
                        "brand_ja": meta.get("brand_ja", ""),
                        "product_name": meta.get("product_name", ""),
                        "feedback_type": fb_type,
                        "content": fb_content,
                        "promoted": False,
                    })
                    st.success(
                        "Chosukeに伝えました。"
                        "**ナレッジ管理モード → フィードバックタブ** で「正式化」にチェックを入れて保存すると、"
                        "次回以降の応答に反映されます。"
                    )


# ============================================================
# 画面2: ナレッジ管理モード
# ============================================================
def knowledge_mode():
    st.markdown("## 📚 ナレッジ管理モード")
    st.caption("管理者(裕平さん)がChosukeの知識を編集・蓄積する画面です。")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏷️ ブランドマスタ",
        "✓ チェックリスト",
        "💬 フィードバック",
        "📋 査定履歴"
    ])

    with tab1:
        st.markdown("### ブランド別 推奨原価率・注意点")
        st.caption(
            "セルをダブルクリックで編集できます。行追加・削除も可能。並び順は日本語名で五十音順を推奨。"
        )
        st.caption(
            "💡 **定番モデル(iconic_models)** はカンマ区切りで登録。"
            "品名に含まれていたらChosukeが「定番モデルですね!」と反応します。"
            "例: `LADY,SADDLE,レディ,サドル`"
        )

        df = load_brands()
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "brand_ja": st.column_config.TextColumn("ブランド(日本語)", required=True),
                "brand_en": st.column_config.TextColumn("ブランド(英語)"),
                "category": st.column_config.SelectboxColumn(
                    "カテゴリ",
                    options=["バッグ", "時計", "ジュエリー", "アパレル", "シューズ", "電子機器", "ステーショナリー", "その他"]
                ),
                "cost_ratio_min": st.column_config.NumberColumn("原価率min(%)", min_value=0, max_value=100),
                "cost_ratio_max": st.column_config.NumberColumn("原価率max(%)", min_value=0, max_value=100),
                "notes": st.column_config.TextColumn("注意点", width="large"),
                "iconic_models": st.column_config.TextColumn(
                    "定番モデル(カンマ区切り)",
                    width="large",
                    help="品名にこのキーワードが含まれたらChosukeが定番モデル反応します。例: LADY,SADDLE,レディ,サドル"
                ),
            },
            key="brands_editor"
        )

        if st.button("💾 ブランドマスタを保存", type="primary"):
            save_brands(edited)
            st.success("保存しました。")
            st.rerun()

    with tab2:
        st.markdown("### ブランド別 細部確認チェックリスト")
        st.caption("各ブランドで確認すべき項目を登録します。")

        df = load_checklists()
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "brand_ja": st.column_config.TextColumn("ブランド(日本語)", required=True),
                "category": st.column_config.SelectboxColumn(
                    "カテゴリ",
                    options=["バッグ", "時計", "ジュエリー", "アパレル", "シューズ", "電子機器", "ステーショナリー", "その他"]
                ),
                "check_item": st.column_config.TextColumn("確認項目", required=True),
                "hint": st.column_config.TextColumn("ヒント/解説", width="large"),
            },
            key="checks_editor"
        )

        if st.button("💾 チェックリストを保存", type="primary"):
            save_checklists(edited)
            st.success("保存しました。")
            st.rerun()

    with tab3:
        st.markdown("### staffから集まったフィードバック")
        st.caption("『正式化』にチェックを入れて保存すると、次回以降Chosukeが該当ブランドの応答時に「ブランドの注意点」として参照します。")

        df = load_feedback()
        if df.empty:
            st.info("まだフィードバックは集まっていません。")
        else:
            df_display = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
            edited = st.data_editor(
                df_display,
                use_container_width=True,
                column_config={
                    "timestamp": st.column_config.TextColumn("日時", disabled=True),
                    "staff": st.column_config.TextColumn("staff", disabled=True),
                    "brand_ja": st.column_config.TextColumn("ブランド", disabled=True),
                    "product_name": st.column_config.TextColumn("品名", disabled=True),
                    "feedback_type": st.column_config.TextColumn("種別", disabled=True),
                    "content": st.column_config.TextColumn("内容", width="large", disabled=True),
                    "promoted": st.column_config.CheckboxColumn("正式化"),
                },
                key="feedback_editor"
            )

            if st.button("💾 正式化状態を保存", type="primary"):
                edited.to_csv(feedback_csv(), index=False, encoding="utf-8-sig")
                st.success("保存しました。")
                st.rerun()

    with tab4:
        st.markdown("### 過去の査定履歴")
        st.caption("Chosukeで相談された全ての査定履歴です。")

        df = load_history()
        if df.empty:
            st.info("まだ履歴がありません。")
        else:
            df_display = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            csv = df_display.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 履歴をCSVダウンロード", csv, "appraisal_history.csv", "text/csv")


# ============================================================
# 画面: 査定レビューモード(裕平さん専用)
# ============================================================
def review_mode():
    st.markdown("## 📝 査定レビューモード")
    st.caption(
        "staffが行った査定について、裕平さんが「実際の原価率」と「コメント」を残す画面です。"
        "ここで蓄積したデータが、次回以降のChosukeの推奨値の精度を上げます。"
    )

    df = load_history()
    if df.empty:
        st.info("まだ査定履歴がありません。")
        return

    # review_status 列がない古い履歴対応
    if "review_status" not in df.columns:
        df["review_status"] = "pending"
    df["review_status"] = df["review_status"].fillna("pending")

    pending = df[df["review_status"] == "pending"].copy()
    reviewed = df[df["review_status"] == "reviewed"].copy()
    skipped = df[df["review_status"] == "skipped"].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("未レビュー", len(pending))
    col2.metric("レビュー済", len(reviewed))
    col3.metric("スキップ", len(skipped))

    st.markdown("---")

    if pending.empty:
        st.success("🦉 未レビューの査定はありません。お疲れさまです!")
        with st.expander("過去のレビュー履歴を確認・修正する"):
            if reviewed.empty and skipped.empty:
                st.caption("まだレビュー履歴はありません。")
            else:
                done = pd.concat([reviewed, skipped]).sort_values("timestamp", ascending=False)
                st.dataframe(
                    done[["timestamp", "staff", "brand_ja", "product_name",
                          "actual_cost_rate", "yuhei_comment", "review_status"]],
                    use_container_width=True, hide_index=True
                )
        return

    # 新しい順にソートして、ドロップダウンで好きな1件を選べるようにする(v0.12.3)
    pending_sorted_all = pending.sort_values("timestamp", ascending=False).reset_index(drop=True)

    # v0.12.3: staff絞り込み
    staff_list = sorted({str(s).strip() for s in pending_sorted_all["staff"].fillna("").tolist() if str(s).strip()})
    staff_filter_options = [t("ui.filter.all")] + staff_list
    selected_staff = st.selectbox(
        t("ui.filter.staff"),
        staff_filter_options,
        key="review_staff_filter",
        help="特定のstaffの査定だけを下のドロップダウンに表示します。",
    )
    if selected_staff == t("ui.filter.all"):
        pending_sorted = pending_sorted_all
    else:
        pending_sorted = pending_sorted_all[
            pending_sorted_all["staff"].fillna("").astype(str).str.strip() == selected_staff
        ].reset_index(drop=True)

    if pending_sorted.empty:
        st.info(f"「{selected_staff}」の未レビュー査定はありません。")
        return

    def _label_for(row) -> str:
        ts = str(row.get("timestamp", ""))[:16].replace("T", " ")
        staff = str(row.get("staff", "") or "")
        brand = str(row.get("brand_ja", "") or "")
        product = str(row.get("product_name", "") or "")
        if len(product) > 40:
            product = product[:38] + "…"
        return f"{ts} / {staff} / {brand} / {product}".strip(" /")

    options = list(range(len(pending_sorted)))
    _filter_suffix = "" if selected_staff == t("ui.filter.all") else f" / staff={selected_staff}"
    selected_idx = st.selectbox(
        f"レビュー対象を選択(全{len(pending_sorted)}件・新しい順{_filter_suffix})",
        options,
        format_func=lambda i: f"{i+1}. {_label_for(pending_sorted.iloc[i])}",
        key="review_target_selector",
    )
    target = pending_sorted.iloc[selected_idx]
    target_idx = df[df["timestamp"] == target["timestamp"]].index[0]

    st.markdown(f"#### 📋 レビュー対象({selected_idx + 1} / {len(pending_sorted)} 件目)")

    with st.container(border=True):
        st.markdown(f"**日時**: {target['timestamp']}")
        st.markdown(f"**staff**: {target.get('staff', '')}")
        st.markdown(f"**ブランド**: {target.get('brand_ja','')} / {target.get('brand_en','')}")
        st.markdown(f"**品名**: {target.get('product_name', '')}")
        st.markdown(f"**製造年**: {target.get('year', '')}")
        st.markdown(f"**付属品**: {target.get('accessories', '')}")
        st.markdown(f"**暫定rank**: {target.get('rank', '')}")
        pmin = target.get("price_min_usd", "")
        pmax = target.get("price_max_usd", "")
        if pmin and pmax:
            st.markdown(f"**相場メモ**: ${pmin} 〜 ${pmax}")
    # --- 相場参考スクショの表示(管理者がレビュー判断するための材料) ---
    try:
        sc_count = int(target.get("screenshots_count", 0) or 0)
    except (ValueError, TypeError):
        sc_count = 0
    # クラウド版: スクショは screenshots タブに shot_id(=査定timestamp)で保存。
    shot_id = str(target.get("screenshot_ids", "") or "").strip()
    if sc_count > 0 or shot_id:
        with st.container(border=True):
            st.markdown(f"##### 🖼️ 相場参考スクショ({sc_count}枚)")
            imgs = []
            if shot_id:
                try:
                    imgs = be.load_screenshots(shot_id)
                except Exception as e:
                    st.caption(f"画像の取得でエラー: {e}")
            if imgs:
                st.caption(t("ui.shot.toggle_caption"))
                # 拡大中の画像インデックスを shot_id 単位で session_state に保持。
                # data: URL の別タブ遷移はブラウザにブロックされるため、画面内トグル方式にする。
                _exp_key = f"expanded_shot::{shot_id}"
                _expanded = st.session_state.get(_exp_key)
                if _expanded is not None:
                    # 拡大表示モード: 選択中の1枚を原寸で表示
                    if 0 <= _expanded < len(imgs):
                        st.image(imgs[_expanded], use_container_width=True)
                    if st.button(t("ui.shot.shrink"), key=f"shrink_{shot_id}"):
                        st.session_state[_exp_key] = None
                        st.rerun()
                else:
                    # サムネイル一覧: 各画像の下に拡大ボタン
                    _cols = st.columns(min(len(imgs), 4))
                    for i, img_bytes in enumerate(imgs):
                        with _cols[i % len(_cols)]:
                            st.image(img_bytes, width=160)
                            if st.button("🔍 拡大 / Expand", key=f"expand_{shot_id}_{i}"):
                                st.session_state[_exp_key] = i
                                st.rerun()
            else:
                # 旧データ(ローカル運用時代の履歴)は画像が紐付いていない。
                st.caption(f"⚠️ 枚数の記録は{sc_count}枚ですが、画像は保存されていません"
                           "(ローカル運用時の履歴)。新しい査定からは画像が表示されます。")

    # --- 査定の評点(管理者向け・プロトタイプ) ---
    comp = score_completeness(target.to_dict() if hasattr(target, "to_dict") else dict(target))
    rng = score_range(target.to_dict() if hasattr(target, "to_dict") else dict(target))
    _emoji = {"充分": "🟢", "ほぼ充分": "🟢", "やや不足": "🟡", "不足": "🔴"}
    _remoji = {"よく絞れている": "🟢", "許容範囲": "🟢", "やや広い": "🟡",
               "広すぎ(要確認)": "🔴", "相場メモなし": "⚪"}
    with st.container(border=True):
        st.markdown("##### 📊 Chosukeの評点(参考)")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"**記載の充分さ**: {_emoji.get(comp['label'],'')} {comp['label']} "
                        f"({comp['filled']}/{comp['total']})")
            if comp["missing"]:
                st.caption("未入力: " + " / ".join(comp["missing"]))
        with sc2:
            rtxt = f"{_remoji.get(rng['label'],'')} {rng['label']}"
            if rng["ratio"]:
                rtxt += f"({rng['ratio']}倍)"
            st.markdown(f"**金額の幅の絞り込み**: {rtxt}")
        st.caption("※あくまで参考値。最終判断は裕平さん。現場には表示されません。")

    st.markdown("##### 🦉 裕平さんの実査定結果")

    with st.form(f"review_form_{target_idx}"):
        actual_rate = st.number_input(
            "実際の原価率(%)",
            min_value=0, max_value=100, step=1,
            help="買取実行時の実際の原価率(価格 ÷ 想定相場)"
        )
        yuhei_comment = st.text_area(
            "コメント(理由・補足)",
            placeholder="例: ピコタンは在庫滞留しやすいので5%下げた / 黒は需要高で強気で出した",
            height=80,
        )
        tags = st.text_input(
            "タグ(任意、カンマ区切り)",
            placeholder="例: 在庫滞留, カラー人気, 急ぎ案件"
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save_btn = st.form_submit_button("💾 保存して次へ", type="primary", use_container_width=True)
        with col_btn2:
            skip_btn = st.form_submit_button(t("ui.training.skip"), use_container_width=True)

        if save_btn:
            df.at[target_idx, "actual_cost_rate"] = actual_rate
            df.at[target_idx, "yuhei_comment"] = yuhei_comment
            df.at[target_idx, "tags"] = tags
            df.at[target_idx, "review_status"] = "reviewed"
            df.at[target_idx, "reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            be.write_sheet("appraisal_history", df)
            st.success("レビュー保存しました。")
            st.rerun()

        if skip_btn:
            df.at[target_idx, "review_status"] = "skipped"
            df.at[target_idx, "reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            be.write_sheet("appraisal_history", df)
            st.info(t("ui.training_review.skipped"))
            st.rerun()





# ============================================================
# 画面: トレーニングモード(本格版) — 査定モードを土台に画像取込+買取金額
# ============================================================
def training_mode():
    st.markdown("## 🎓 " + t("ui.mode.training"))
    st.caption(t("ui.training.caption"))

    # number_input の +/- ステッパーを隠す(現場フィードバック: 不要)
    st.markdown("""
        <style>
        [data-testid="stNumberInput"] button {display:none;}
        </style>
    """, unsafe_allow_html=True)

    # トレーニングは2タブ構成: 提出 / 自分の結果
    tab_submit, tab_results = st.tabs([t("ui.training.tab.submit"), t("ui.training.tab.results")])
    with tab_results:
        _training_my_results()
    with tab_submit:
        _training_submit_panel()


def _training_submit_panel():

    if "t_advice_result" not in st.session_state:
        st.session_state.t_advice_result = None
    if "t_advice_meta" not in st.session_state:
        st.session_state.t_advice_meta = {}

    col_input, col_output = st.columns([1, 1.3], gap="large")

    # ----- 左: 商品情報入力 -----
    with col_input:
        # ===== 担当staff(最上部・必須項目) =====
        # v0.12.4: フリーテキスト入力(text_input)による表記ゆれ(Komatsu/komastu/komatu…)を
        #   防ぐため、staff_master.csv からの選択式(selectbox)に変更。
        #   「(➕ 新規staffを追加)」を選んだときだけ入力欄を出し、確定した名前はマスタへ自動登録する。
        #   ※固定キー apprai_staff の意味は「最終的に確定したstaff名」を保持する点で従来どおり。
        #     クリア時に残す挙動(_clear_appraisal_inputs が触らない)も維持される。
        st.markdown("### " + t("ui.staff.header"))

        _STAFF_NEW_OPTION = "(➕ 新規staffを追加)"
        staff_options = load_staff_master()
        # クラウド版: 表記ゆれ再発防止のため、新規staff追加は管理者のみ。
        # staff ロールでは選択肢に「新規追加」を出さない(選ぶだけ)。
        _is_admin = st.session_state.get("role") == "admin"
        if _is_admin:
            staff_select_options = staff_options + [_STAFF_NEW_OPTION]
        else:
            staff_select_options = staff_options

        # 既に確定済みのstaff(apprai_staff)があれば、それを初期選択にする。
        _current_staff = str(st.session_state.get("train_examinee", "") or "").strip()
        if _current_staff and _current_staff in staff_options:
            _staff_index = staff_options.index(_current_staff)
        else:
            _staff_index = None

        _staff_choice = st.selectbox(
            t("ui.staff.header"),
            staff_select_options,
            index=_staff_index,
            placeholder=t("ui.staff.placeholder"),
            key="train_examinee_select",
            label_visibility="collapsed",
            help=t("ui.staff.help")
        )

        if _is_admin and _staff_choice == _STAFF_NEW_OPTION:
            _staff_new = st.text_input(
                "新しいstaff名",
                key="train_examinee_new",
                placeholder=t("ui.settings.staff_placeholder"),
                help=t("ui.staff.add_help")
            ).strip()
            staff = _staff_new
            if _staff_new:
                # 新規入力された名前をマスタに登録(次回以降は選択肢に出る)
                add_staff_to_master(_staff_new)
        elif _staff_choice:
            staff = _staff_choice
        else:
            staff = ""

        # 確定したstaff名を固定キーに反映(履歴保存・クリア後の保持はこのキーを使う)
        st.session_state["train_examinee"] = staff

        if not staff.strip():
            st.caption("⚠️ " + t("ui.staff.required"))

        st.markdown("### " + t("ui.product.header"))

        brands_df = load_brands()
        brands_df_sorted = brands_df.sort_values("brand_ja").reset_index(drop=True)

        # まずカテゴリを「内部状態」として保持(UIは後で出す)
        # ※ブランド絞り込みに使うため、現在の選択値を先読みする。
        #   v0.10.9: nonce方式に伴い、カテゴリの現在値も nonce 付きキーから読む。
        #   クリア直後は nonce が変わって該当キーが無い → 「指定なし」になる。
        selected_category = st.session_state.get(_tk("category"), "指定なし")

        # カテゴリでブランドを絞り込み(現在の選択値を使う)
        # v0.10.6: 絞り込み結果が0件になったら自動で全ブランド表示に戻す(フォールバック)。
        #   ハイブランドは1ブランドで多カテゴリ(バッグ/財布/スカーフ/時計…)を扱うのが実態。
        #   マスタの category は1ブランド1値しか持てないため、スカーフ・アクセサリー等を選ぶと
        #   ヴィトン等の主要ブランドが候補から消える取りこぼしが起きていた(査定不能になる)。
        #   → ブランドを消さないことを最優先にし、該当0件なら絞り込みを無効化する。
        if selected_category != "指定なし":
            def _matches_category(master_cat: str) -> bool:
                normalized = BRAND_CATEGORY_NORMALIZE.get(master_cat, master_cat)
                return normalized == selected_category

            candidate_df = brands_df_sorted[
                brands_df_sorted["category"].apply(_matches_category)
            ].reset_index(drop=True)

            if len(candidate_df) > 0:
                filtered_df = candidate_df
            else:
                # 該当ブランドが1件も無い → 絞り込みを諦めて全ブランド表示に戻す
                filtered_df = brands_df_sorted
        else:
            filtered_df = brands_df_sorted

        brand_labels = [
            f"{row['brand_ja']}  /  {row['brand_en']}"
            for _, row in filtered_df.iterrows()
        ] + ["(その他/未登録)"]

        # v0.10.7: フォールバック時の案内文は削除(現場フィードバック: 不要・くどい)。
        #   ブランドが消えない挙動(フォールバック)はそのまま維持。
        #   絞り込めない場合は黙って全ブランドを出すのが自然な体験。

        # ブランド選択(カテゴリより上に表示)
        sel_label = st.selectbox(
            t("ui.brand.label"),
            brand_labels,
            index=None,
            placeholder=t("ui.brand.placeholder"),
            key=_tk("brand_label")
        )

        # カテゴリ選択(ブランドの下・絞り込みフィルタ)
        # ※key="apprai_category" は session_state で復元されるので index 指定不要
        selected_category = st.selectbox(
            t("ui.category.label"),
            CATEGORY_OPTIONS,
            format_func=_category_display,
            key=_tk("category"),
            help=t("ui.category.help")
        )

        if sel_label is None:
            brand_ja = ""
            brand_en = ""
        elif sel_label == "(その他/未登録)":
            brand_ja = st.text_input(t("ui.brand.name_ja"), key=_tk("brand_custom_ja"))
            brand_en = st.text_input(t("ui.brand.name_en"), key=_tk("brand_custom_en"))
        else:
            parts = sel_label.split("  /  ")
            brand_ja = parts[0]
            brand_en = parts[1] if len(parts) > 1 else ""

        product_name = st.text_input(t("ui.product.label"), value="", placeholder=t("ui.product.placeholder"), key=_tk("product"))

        col_y, col_r = st.columns([1, 1])
        with col_y:
            year = st.text_input(t("ui.year.label"), placeholder=t("ui.year.placeholder"), key=_tk("year"))
        with col_r:
            rank = st.selectbox(t("ui.rank.label"), RANK_OPTIONS, format_func=_rank_display, key=_tk("rank"))

        # 付属品は単独行(直下に「一部欠品」の詳細チェックリストを出すため)
        # ※ option の値("フルセット"等)は履歴保存・判定ロジックで使う固定キーなので翻訳しない。
        #   表示だけ format_func で言語切替する。
        _ACC_LABEL = {
            "フルセット": "ui.acc.full",
            "一部欠品": "ui.acc.partial",
            "本体のみ": "ui.acc.bodyonly",
        }
        accessories_status = st.selectbox(
            t("ui.acc.label"),
            ["フルセット", "一部欠品", "本体のみ"],
            format_func=lambda v: t(_ACC_LABEL.get(v, v)),
            key=_tk("acc_status")
        )

        # 「一部欠品」のときだけ詳細チェックリストを表示
        # (付属品プルダウンの直下に置くことで、選択→入力の視線が途切れないようにする)
        accessories_detail = ""
        missing_items = []  # 欠品品目(一部欠品以外では空のまま → Chosukeの欠品コメントも出ない)
        if accessories_status == "一部欠品":
            with st.container(border=True):
                st.caption(t("ui.acc.missing_prompt"))

                # 主要項目(常に表示)
                main_items = ["箱", "保存袋", "ギャランティーカード",
                              "取扱説明書(取説)", "鍵・カデナ", "ストラップ"]
                main_cols = st.columns(2)
                for i, item in enumerate(main_items):
                    with main_cols[i % 2]:
                        if st.checkbox(item, key=_tk(f"acc_main_{item}")):
                            missing_items.append(item)

                # 「もっと見る」展開
                with st.expander(t("ui.more_fields")):
                    extra_items = ["内箱", "外箱", "化粧箱", "レシート・購入証明",
                                   "シリアルカード", "ショッピングバッグ(紙袋)",
                                   "予備コマ", "タグ"]
                    extra_cols = st.columns(2)
                    for i, item in enumerate(extra_items):
                        with extra_cols[i % 2]:
                            if st.checkbox(item, key=_tk(f"acc_extra_{item}")):
                                missing_items.append(item)

                    other_text = st.text_input(
                        "その他(自由記述)",
                        placeholder=t("ui.acc.other_placeholder"),
                        key=_tk("acc_other")
                    )
                    if other_text.strip():
                        missing_items.append(f"その他: {other_text.strip()}")

                accessories_detail = ", ".join(missing_items) if missing_items else "(欠品項目未指定)"

        # ギャランティーカード有無 (v0.10: 推奨原価率の動的算出に使用)
        # ※ option値は下の gc_status マップのキーなので翻訳しない。表示のみ format_func で切替。
        _GC_LABEL = {
            "対象外 / 不問": "ui.gc.na",
            "有り": "ui.gc.has",
            "無し": "ui.gc.none",
        }
        gc_choice = st.radio(
            t("ui.gc.label"),
            ["対象外 / 不問", "有り", "無し"],
            format_func=lambda v: t(_GC_LABEL.get(v, v)),
            horizontal=True,
            key=_tk("gc"),
            help=t("ui.gc.help")
        )
        gc_status = {"有り": "has", "無し": "none", "対象外 / 不問": "na"}[gc_choice]

        # 製造年の補助フラグ: マイクロチップ品 / 年式不明 / ランダムシリアル品
        col_chip, col_unknown, col_random = st.columns(3)
        with col_chip:
            is_microchip = st.checkbox(
                t("ui.flag.microchip"),
                key=_tk("microchip"),
                help=t("ui.microchip.help")
            )
        with col_unknown:
            is_year_unknown = st.checkbox(
                t("ui.flag.year_unknown"),
                key=_tk("year_unknown"),
                help=t("ui.year_unknown.help")
            )
        with col_random:
            is_random_serial = st.checkbox(
                t("ui.flag.random_serial"),
                key=_tk("random_serial"),
                help=t("ui.random_serial.help")
            )

        # 履歴・応答ロジック用に付属品情報を文字列化
        if accessories_status == "フルセット":
            accessories = "フルセット"
        elif accessories_status == "本体のみ":
            accessories = "本体のみ"
        else:  # 一部欠品
            accessories = f"一部欠品 [{accessories_detail}]" if accessories_detail else "一部欠品"

        # ブランド固有: 刻印・シリアル入力
        stamp_or_serial = ""
        if brand_en in ("HERMES", "CHANEL", "ROLEX"):
            label_map = {
                "HERMES": "刻印(例: A, ○A, □R, R など)",
                "CHANEL": "シリアル番号(7桁または8桁)",
                "ROLEX": "シリアル番号(数字または英数字)",
            }
            stamp_or_serial = st.text_input(
                label_map[brand_en],
                placeholder=t("ui.serial.placeholder"),
                key=_tk("stamp")
            )

        # ===== 現物写真(全体+査定ポイント): 相談前に入力 =====
        st.markdown("### 🖼️ " + t("ui.training.img.header"))
        st.info("📷 **査定している“現物”の写真** をここに入れてください。"
                "相場スクショ(画面)ではありません。/ Photos of the **actual item** (not market screenshots).")
        st.markdown("**" + t("ui.training.img.overall") + "**")
        st.caption(t("ui.training.img.overall_caption"))
        overall_file = st.file_uploader(
            "📷 " + t("ui.training.img.overall"), type=["png", "jpg", "jpeg"],
            accept_multiple_files=False, key=_tk("img_overall"))
        if overall_file is not None:
            _oc = st.columns([1, 3])
            with _oc[0]:
                st.image(overall_file, width=110, caption="📷 全体")
        st.markdown("**" + t("ui.training.img.points") + "**")
        st.caption(t("ui.training.img.points_caption"))
        point_files = st.file_uploader(
            "📷 " + t("ui.training.img.points"), type=["png", "jpg", "jpeg"],
            accept_multiple_files=True, key=_tk("img_points"))
        if point_files and len(point_files) > 5:
            st.warning("査定ポイント画像は最大5枚です。先頭5枚のみ使用します。")
            point_files = point_files[:5]
        if point_files:
            st.caption(f"📷 査定ポイント {len(point_files)}枚")
            _pc = st.columns(min(len(point_files), 5))
            for _i, _f in enumerate(point_files):
                with _pc[_i % len(_pc)]:
                    st.image(_f, width=100, caption=f"📷 ポイント{_i+1}")

        st.markdown("### " + t("ui.market.header"))
        st.caption(t("ui.market.caption"))
        col_pmin, col_pmax = st.columns(2)
        with col_pmin:
            price_min = st.number_input(t("ui.market.min"), min_value=0, step=1, format="%d", key=_tk("pmin"))
        with col_pmax:
            price_max = st.number_input(t("ui.market.max"), min_value=0, step=1, format="%d", key=_tk("pmax"))

        st.markdown("### " + t("ui.screenshot.header"))
        st.info("💻 **相場を調べた“画面”のスクショ** をここに入れてください(ネット・他店の売値など)。"
                "現物の写真ではありません。/ Screenshots of **market price screens** (not the actual item).")
        st.caption(t("ui.screenshot.caption"))
        uploaded_files = st.file_uploader(
            "💻 相場スクショをドラッグ&ドロップ / Market screenshots",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=_tk("screenshots")
        )
        if uploaded_files:
            st.caption(f"📊 相場参考スクショ {len(uploaded_files)}枚 をアップしました")
            _prev_cols = st.columns(min(len(uploaded_files), 4))
            for _i, _f in enumerate(uploaded_files):
                with _prev_cols[_i % len(_prev_cols)]:
                    st.image(_f, width=110, caption=f"📊 相場{_i+1}")

        # 画像入力(全体・査定ポイント)は相談後に表示するため、ここでは描画しない
        # 「Chosukeに相談する」: 商品情報が揃えば押せる(画像・金額は提出時に必須)
        staff_filled = bool(staff.strip())
        brand_filled = bool(brand_ja and brand_ja.strip())
        consult_ready = staff_filled and brand_filled
        if not staff_filled:
            btn_help = t("ui.training.need_examinee")
        elif not brand_filled:
            btn_help = t("ui.brand.need")
        else:
            btn_help = None
        ask_chosuke = st.button(
            t("ui.training.consult"),
            type="primary",
            use_container_width=True,
            disabled=not consult_ready,
            help=btn_help,
            key="train_consult_btn",
        )

    # ----- 「Chosukeに相談する」押下: 応答を生成し、入力スナップショットを保持(保存はしない) -----
    if ask_chosuke and brand_ja and product_name and staff.strip():
        advice = chosuke_advise(
            brand_ja, brand_en, product_name, year, accessories,
            (len(uploaded_files) if uploaded_files else 0), rank,
            price_min, price_max, stamp_or_serial,
            is_microchip, is_year_unknown,
            is_random_serial=is_random_serial,
            gc_status=gc_status,
            assess_cat=(selected_category if selected_category != "指定なし" else ""),
            accessories_status=accessories_status,
            missing_items=missing_items,
        )
        st.session_state.t_advice_result = advice
        st.session_state.t_advice_meta = {
            "brand_ja": brand_ja, "brand_en": brand_en,
            "product_name": product_name, "staff": staff,
        }
        # 提出時に使う入力スナップショット(相談時点の値を保持)
        st.session_state["t_pending"] = {
            "staff": staff, "brand_ja": brand_ja, "brand_en": brand_en,
            "category": selected_category if selected_category != "指定なし" else "",
            "product_name": product_name, "year": year, "accessories": accessories,
            "rank": rank,
            "price_min": price_min, "price_max": price_max,
        }
        # 新しい相談をしたら、前回の提出完了フラグはリセット
        st.session_state.pop("t_submitted_done", None)


    # ----- 右: Chosukeの応答 -----
    with col_output:
        st.markdown("### " + t("ui.response.header"))

        if st.session_state.t_advice_result is None:
            if ask_chosuke:
                st.warning(t("ui.need_brand_product"))
            else:
                st.info(t("ui.response.empty"))
        else:
            advice = st.session_state.t_advice_result
            meta = st.session_state.t_advice_meta

            st.markdown(f"""
            <div class="chosuke-bubble">
                <div class="chosuke-name">🦉 Chosuke</div>
                <div class="chosuke-text">{advice["bubble_msg"]}</div>
            </div>
            """, unsafe_allow_html=True)

            if advice.get("range_info"):
                ri = advice["range_info"]
                level = ri["level"]
                if level != "unknown":
                    st.markdown(f"""
                    <div class="range-card-{level}">
                        <strong>{t("ui.card.range_header")}</strong><br>
                        {ri["message"]}
                    </div>
                    """, unsafe_allow_html=True)

            if advice["cost_min"] is not None:
                _src = advice.get("cost_source")
                if _src == "実績":
                    source_label = t("dyn.card.cost_src_actual", n=advice.get('cost_actual_count', 0))
                elif _src == "動的算出":
                    source_label = t("ui.card.cost_src_dynamic")
                else:
                    source_label = t("ui.card.cost_src_initial")
                st.markdown(f"""
                <div class="cost-ratio-card">
                    <div class="cost-ratio-label">{t("ui.card.cost_label", src=source_label)}</div>
                    <div class="cost-ratio-value">{advice["cost_min"]}% 〜 {advice["cost_max"]}%</div>
                    <div class="cost-ratio-note">{t("ui.card.cost_note")}</div>
                    <div class="cost-ratio-cheer">🦉 {t("msg.negotiation_prompt")}</div>
                </div>
                """, unsafe_allow_html=True)

                # v0.10: 思考過程カード (動的算出時のみ)
                # 設計インサイト #004: 数字だけでなく「どう考えたか」を見せる
                if advice.get("cost_thinking"):
                    st.markdown(f"""
                    <div class="thinking-card">
                        <div class="thinking-label">{t("ui.card.thinking_label")}</div>
                        <div class="thinking-text">{advice["cost_thinking"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # v0.10.1: 確認動作カード (Layerに関係なく常時表示)
            # 設計インサイト #004: 鑑定士の手を止めさせ、具体動作(ルーペ/ライト等)を促す。
            # 原価率の算出方法(実績/動的/初期値)に関わらず、カテゴリが分かれば必ず出す。
            if advice.get("inspection_tip"):
                _ins_cat = advice.get("inspect_cat") or t("ui.card.inspect_default_cat")
                st.markdown(f"""
                <div class="inspection-card">
                    <div class="inspection-label">{t("dyn.card.inspection_label", cat=_ins_cat)}</div>
                    <div class="inspection-text">{advice["inspection_tip"]}</div>
                </div>
                """, unsafe_allow_html=True)

            # v0.10.4: 欠品アドバイスカード (一部欠品で品目チェックがあるときだけ)
            # 設計インサイト #002: 欠品を断定減額せず、観察を促す。
            if advice.get("missing_advice"):
                st.markdown(f"""
                <div class="missing-card">
                    <div class="missing-label">📦 付属品の欠品について</div>
                    <div class="missing-text">{advice["missing_advice"]}</div>
                </div>
                """, unsafe_allow_html=True)

            if advice.get("year_advice"):
                st.markdown(f"""
                <div class="year-card">
                    <strong>{t("ui.card.year_label")}</strong><br>
                    {advice["year_advice"]}
                </div>
                """, unsafe_allow_html=True)

            # v0.9: 年式タグ反応 (いかりや長介トーン)
            if advice.get("year_tag_msg"):
                st.markdown(f"""
                <div class="year-tag-card">
                    <strong>🦉 Chosukeより一言</strong><br>
                    {advice["year_tag_msg"]}
                </div>
                """, unsafe_allow_html=True)

            if advice.get("history_msg"):
                st.markdown(f"""
                <div class="history-card">
                    <strong>{t("ui.card.history_label")}</strong><br>
                    {advice["history_msg"]}
                </div>
                """, unsafe_allow_html=True)

            # 注意点(統合表示)
            notes_items = []
            if advice["brand_notes"]:
                notes_items.append({"src": t("ui.card.notes_src_initial"), "content": td(advice["brand_notes"], st.session_state.lang)})
            if not advice["past_feedback"].empty:
                for _, row in advice["past_feedback"].iterrows():
                    notes_items.append({
                        "src": t("ui.card.notes_src_feedback", type=row.get('feedback_type','')),
                        "content": row["content"]
                    })

            if notes_items:
                st.markdown("#### " + t("ui.card.brand_notes"))
                for item in notes_items:
                    with st.container(border=True):
                        st.markdown(f"_{item['src']}_")
                        st.markdown(item["content"])

            # チェック項目
            # 「相場根拠は充分か?」を全カテゴリ共通の先頭固定項目として表示
            st.markdown("#### " + t("ui.card.checklist"))
            with st.container(border=True):
                st.checkbox(
                    f"**{t('ui.checklist.baseline_item')}**",
                    key=f"chk_baseline_{meta.get('brand_ja','')}_{meta.get('product_name','')}"
                )
                st.caption(t("ui.checklist.baseline_hint"))

            # ブランド固有のチェックリスト
            if not advice["checklists"].empty:
                for idx, row in advice["checklists"].iterrows():
                    chk_key = f"chk_{meta.get('brand_ja','')}_{idx}_{row['check_item']}"
                    with st.container(border=True):
                        st.checkbox(f"**{td(row['check_item'], st.session_state.lang)}**", key=chk_key)
                        st.caption(td(row["hint"], st.session_state.lang))

            # ===== 応答を見た後: 自分の買取金額 + 提出 =====
            # (現物写真は相談前セクションで入力済み)
            st.markdown("---")
            st.markdown("### 💰 " + t("ui.training.offer.header"))
            st.caption(t("ui.training.offer.after_consult"))
            staff_offer = st.number_input(
                t("ui.training.offer.label"), min_value=0, step=1, format="%d", key=_tk("offer"))

            overall_ok = overall_file is not None
            offer_ok = staff_offer > 0
            submit_ready = overall_ok and offer_ok
            if not overall_ok:
                sub_help = t("ui.training.need_overall")
            elif not offer_ok:
                sub_help = t("ui.training.need_offer")
            else:
                sub_help = None

            already = st.session_state.get("t_submitted_done")
            if already:
                st.success("🦉 " + t("ui.training.submitted"))
            else:
                do_submit = st.button(
                    t("ui.training.tab.submit"), type="primary", use_container_width=True,
                    disabled=not submit_ready, help=sub_help, key="train_submit_btn")
                if do_submit and submit_ready:
                    snap = st.session_state.get("t_pending", {})
                    _ts_iso = datetime.now().isoformat(timespec="seconds")
                    # 相場参考スクショ(②): shot_id "ts::market"
                    market_shot_id = _ts_iso + "::market"
                    market_count = 0
                    if uploaded_files:
                        market_count = len(uploaded_files)
                        for i, f in enumerate(uploaded_files):
                            try:
                                be.save_screenshot(market_shot_id, i, f.read())
                            except Exception as ex:
                                st.warning(f"相場スクショ保存に失敗({f.name}): {ex}")
                    # 商品画像(①③): shot_id "ts::item" idx0=全体, idx1..=ポイント
                    item_shot_id = _ts_iso + "::item"
                    item_count = 0
                    try:
                        be.save_screenshot(item_shot_id, 0, overall_file.read())
                        item_count += 1
                        for j, pf in enumerate(point_files or [], start=1):
                            be.save_screenshot(item_shot_id, j, pf.read())
                            item_count += 1
                    except Exception as ex:
                        st.warning(f"商品画像の保存に失敗: {ex}")

                    append_training({
                        "timestamp": _ts_iso,
                        "staff": snap.get("staff", ""),
                        "brand_ja": snap.get("brand_ja", ""),
                        "brand_en": snap.get("brand_en", ""),
                        "category": snap.get("category", ""),
                        "product_name": snap.get("product_name", ""),
                        "year": snap.get("year", ""),
                        "accessories": snap.get("accessories", ""),
                        "rank": snap.get("rank", ""),
                        "price_min_usd": snap.get("price_min") if snap.get("price_min", 0) else "",
                        "price_max_usd": snap.get("price_max") if snap.get("price_max", 0) else "",
                        "image_count": item_count,
                        "staff_offer_price": staff_offer,
                        "screenshot_ids": f"{market_shot_id}|{item_shot_id}",
                        "review_status": "pending",
                        "submitted_at": _ts_iso,
                        "eval_input": "", "eval_market_image": "", "eval_rank": "",
                        "expert_answer_min": "", "expert_answer_max": "",
                        "expert_answer_price": "", "price_gap": "",
                        "overall_mark": "", "eval_comment": "", "reviewed_at": "",
                    })
                    st.session_state["t_submitted_done"] = True
                    st.toast("✅ 提出しました!裕平さんの評価を待ちましょう。")
                    st.rerun()


# ============================================================
# 画面2: ナレッジ管理モード
# ============================================================


def _training_my_results():
    """staff が自分のトレーニング評価結果を確認する画面(緩い運用: 名前を選ぶだけ)。"""
    st.caption(t("ui.training.myresults.caption"))
    df = load_training()
    if df.empty:
        st.info(t("ui.training.myresults.none"))
        return
    if "review_status" not in df.columns:
        df["review_status"] = "pending"
    df["review_status"] = df["review_status"].fillna("pending")

    staff_options = load_staff_master()
    who = st.selectbox(t("ui.training.examinee"), staff_options, index=None,
                       placeholder=t("ui.staff.placeholder"), key="myresults_who")
    if not who:
        return

    mine = df[(df["staff"].astype(str).str.strip() == who) &
              (df["review_status"] == "reviewed")].copy()
    if mine.empty:
        st.info(t("ui.training.myresults.none"))
        return

    mine = mine.sort_values("timestamp", ascending=False)
    _MARK_DISP = {
        "hanamaru": t("ui.training_review.mark.hanamaru"),
        "yoku": t("ui.training_review.mark.yoku"),
        "ganbaro": t("ui.training_review.mark.ganbaro"),
    }
    for _, row in mine.iterrows():
        ts = str(row.get("timestamp", ""))[:16].replace("T", " ")
        brand = row.get("brand_ja", "")
        product = row.get("product_name", "")
        mark = _MARK_DISP.get(str(row.get("overall_mark", "")), "")
        _row_ts = str(row.get("timestamp", "")).replace(":", "").replace("-", "").replace("T", "")
        with st.container(border=True):
            st.markdown(f"#### {mark}")
            st.caption(f"{ts} / {brand} / {product}")

            # --- 自分が当時どう査定したか(振り返り用・提出内容フル) ---
            with st.expander(t("ui.training.view_own"), expanded=True):
                st.markdown(f"**ブランド**: {brand} / {row.get('brand_en','')}")
                st.markdown(f"**品名**: {product}")
                st.markdown(f"**製造年**: {row.get('year','') or '—'}")
                st.markdown(f"**付属品**: {row.get('accessories','') or '—'}")
                st.markdown(f"**暫定rank**: {row.get('rank','') or '—'}")
                _pmin = row.get("price_min_usd", "")
                _pmax = row.get("price_max_usd", "")
                if _pmin and _pmax:
                    st.markdown(f"**相場メモ**: ${_pmin} 〜 ${_pmax}")
                # 自分がアップした画像(商品画像 + 相場参考スクショ)
                raw_ids = str(row.get("screenshot_ids", "") or "").strip()
                _mkt_id, _item_id = "", ""
                if "|" in raw_ids:
                    _parts = raw_ids.split("|", 1)
                    _mkt_id = _parts[0].strip()
                    _item_id = _parts[1].strip() if len(_parts) > 1 else ""
                elif raw_ids:
                    _item_id = raw_ids
                _show_shot_group(_item_id, "🖼️ 商品画像(全体 + 査定ポイント)",
                                 key_prefix=f"my_item_{_row_ts}", point_label_overall=True)
                _show_shot_group(_mkt_id, "📊 相場参考スクショ",
                                 key_prefix=f"my_market_{_row_ts}", point_label_overall=False)

            # 自分の提出 vs 正解レンジ
            emin = row.get("expert_answer_min", "")
            emax = row.get("expert_answer_max", "")
            offer = row.get("staff_offer_price", "")
            if emin and emax:
                ans = f"${emin} 〜 ${emax}"
            elif row.get("expert_answer_price", ""):
                ans = f"${row.get('expert_answer_price')}"
            else:
                ans = "—"
            cols = st.columns(2)
            cols[0].metric("あなたの買取金額", f"${offer}")
            cols[1].metric("正解の買取金額", ans)
            # 4軸(v0.13.1: 3段階対応 + 旧2択の後方互換)
            _ev = {
                "適切": "🟢", "少し改善": "🟡", "要改善": "🔴",
                # --- 旧表記の後方互換 ---
                "要改善 ": "🔴", "Good": "🟢", "Needs work": "🔴",
            }
            def _e(v): return f"{_ev.get(str(v).strip(), '⚪')} {v}" if v else "—"
            st.markdown(
                f"- {t('ui.training_review.axis1')}: {_e(row.get('eval_input',''))}\n"
                f"- {t('ui.training_review.axis2')}: {_e(row.get('eval_market_image',''))}\n"
                f"- {t('ui.training_review.axis3')}: {_e(row.get('eval_rank',''))}"
            )
            comment = str(row.get("eval_comment", "") or "")
            if comment:
                st.markdown("**🦉 " + t("ui.training_review.comment") + "**")
                st.info(comment)


def _tk(base: str) -> str:
    """トレーニング入力ウィジェットのキー(査定モードと衝突しない専用 nonce 付き)。"""
    n = st.session_state.get("_train_nonce", 0)
    return f"train_{base}_{n}"


def _show_shot_group(shot_id: str, title: str, key_prefix: str, point_label_overall: bool = False):
    """指定 shot_id の画像群を、査定レビューと同じ画面内トグル方式で表示する。
    point_label_overall=True のとき idx0 を『全体』、idx>=1 を『査定ポイントN』とバッジ表示。"""
    if not shot_id:
        return
    try:
        imgs = be.load_screenshots(shot_id)
    except Exception as e:
        st.caption(f"画像の取得でエラー: {e}")
        return
    if not imgs:
        return
    st.markdown(f"##### {title}")
    st.caption(t("ui.shot.toggle_caption"))
    _exp_key = f"train_expanded::{shot_id}"
    _expanded = st.session_state.get(_exp_key)
    if _expanded is not None and 0 <= _expanded < len(imgs):
        st.image(imgs[_expanded], use_container_width=True)
        if point_label_overall:
            cap = "全体画像" if _expanded == 0 else f"査定ポイント {_expanded}"
            st.caption(f"📍 {cap}")
        if st.button(t("ui.shot.shrink"), key=f"{key_prefix}_shrink"):
            st.session_state[_exp_key] = None
            st.rerun()
    else:
        cols = st.columns(min(len(imgs), 3))
        for i, img_bytes in enumerate(imgs):
            with cols[i % len(cols)]:
                st.image(img_bytes, width=160)
                if point_label_overall:
                    badge = "🟢 全体" if i == 0 else f"🔍 ポイント{i}"
                else:
                    badge = f"🖼️ {i+1}"
                if st.button(f"{badge} / Expand", key=f"{key_prefix}_expand_{i}"):
                    st.session_state[_exp_key] = i
                    st.rerun()


def training_review_mode():
    """🎓 トレーニング評価モード(管理者側)。
    staff が提出したトレーニングを、現物画像(全体+査定ポイント)と相場参考スクショを
    見ながら4軸で評価する: ①商品入力 ②相場参考画像 ③Rank ④買取金額。
    点数化はせず、総合は花丸3段階マークで返す。"""
    st.markdown("## 🎓 " + t("ui.mode.training_review"))
    st.caption(t("ui.training_review.caption"))

    # --- 直近の Slack 通知結果(rerun でも消えないよう常時表示) ---
    _lsr = st.session_state.get("last_slack_result")
    if _lsr:
        _staff = _lsr.get("staff", "")
        _sid = _lsr.get("slack_id", "")
        _at = _lsr.get("at", "")
        if _lsr.get("ok"):
            st.success(f"✅ Slack通知を送信しました → {_staff}({_sid})  [{_at}]")
        else:
            _why = _lsr.get("why", "")
            _reason = {
                "no_slack_id": "Slack IDが未登録です(設定モードで登録してください)",
                "no_token": "SLACK_BOT_TOKEN が未設定です",
                "not_in_channel": "BotがそのユーザーにDMを送れません(im:write スコープを追加してください)",
                "channel_not_found": "Slack IDが見つかりません(U… の形式か確認してください)",
            }.get(_why, _why)
            st.error(f"⚠️ Slack通知 失敗 → {_staff}({_sid})  理由: {_reason}  [{_at}]")
        with st.expander("📨 送信しようとした内容を見る"):
            st.code(_lsr.get("dm", ""), language=None)
        if st.button("この通知ログを消す", key="clear_slack_log"):
            st.session_state.pop("last_slack_result", None)
            st.rerun()

    df = load_training()
    if df.empty:
        st.info(t("ui.training.no_submit"))
        return

    if "review_status" not in df.columns:
        df["review_status"] = "pending"
    df["review_status"] = df["review_status"].fillna("pending")

    pending = df[df["review_status"] == "pending"].copy()
    reviewed = df[df["review_status"] == "reviewed"].copy()

    c1, c2 = st.columns(2)
    c1.metric("未評価", len(pending))
    c2.metric("評価済", len(reviewed))

    # v0.13.1 (項目2): 未評価のstaff別残数を表示
    if not pending.empty:
        _pend_counts = (
            pending["staff"].fillna("(不明)").astype(str).str.strip()
            .replace("", "(不明)").value_counts()
        )
        _breakdown = " / ".join(f"{name} {cnt}件" for name, cnt in _pend_counts.items())
        st.caption("👤 未評価の内訳: " + _breakdown)

    # v0.13.1 (項目3): 評価済履歴を常時表示(staff別絞り込みつき)
    with st.expander(f"📚 評価済の履歴を見る({len(reviewed)}件)"):
        if reviewed.empty:
            st.caption(t("ui.training_review.no_history"))
        else:
            _rev_staff = sorted({
                str(s).strip() for s in reviewed["staff"].fillna("").tolist() if str(s).strip()
            })
            _sel_rev_staff = st.selectbox(
                "staff絞り込み", [t("ui.filter.all")] + _rev_staff,
                key="train_review_history_staff_filter")
            _done = reviewed.copy()
            if _sel_rev_staff != t("ui.filter.all"):
                _done = _done[
                    _done["staff"].fillna("").astype(str).str.strip() == _sel_rev_staff
                ]
            _done = _done.sort_values("timestamp", ascending=False)
            show_cols = [c for c in ["timestamp", "staff", "brand_ja", "product_name",
                         "staff_offer_price", "expert_answer_min", "expert_answer_max",
                         "price_gap", "overall_mark", "eval_comment"] if c in _done.columns]
            st.caption(f"{len(_done)}件")
            st.dataframe(_done[show_cols], use_container_width=True, hide_index=True)

    st.markdown("---")

    if pending.empty:
        st.success(t("ui.training_review.none_pending"))
        return

    pending_sorted_all = pending.sort_values("timestamp", ascending=False).reset_index(drop=True)
    staff_list = sorted({str(s).strip() for s in pending_sorted_all["staff"].fillna("").tolist() if str(s).strip()})
    sel_staff = st.selectbox(t("ui.filter.staff"), [t("ui.filter.all")] + staff_list, key="train_review_staff_filter")
    if sel_staff == t("ui.filter.all"):
        pending_sorted = pending_sorted_all
    else:
        pending_sorted = pending_sorted_all[
            pending_sorted_all["staff"].fillna("").astype(str).str.strip() == sel_staff
        ].reset_index(drop=True)

    if pending_sorted.empty:
        st.info(f"「{sel_staff}」の未評価提出はありません。")
        return

    def _label_for(row) -> str:
        ts = str(row.get("timestamp", ""))[:16].replace("T", " ")
        staff = str(row.get("staff", "") or "")
        brand = str(row.get("brand_ja", "") or "")
        product = str(row.get("product_name", "") or "")
        if len(product) > 40:
            product = product[:38] + "…"
        return f"{ts} / {staff} / {brand} / {product}".strip(" /")

    options = list(range(len(pending_sorted)))
    sel_idx = st.selectbox(
        f"評価対象を選択(全{len(pending_sorted)}件・新しい順)",
        options, format_func=lambda i: f"{i+1}. {_label_for(pending_sorted.iloc[i])}",
        key="train_review_target_selector")
    target = pending_sorted.iloc[sel_idx]
    target_idx = df[df["timestamp"] == target["timestamp"]].index[0]

    st.markdown(f"#### 📋 提出内容({sel_idx + 1} / {len(pending_sorted)} 件目)")

    with st.container(border=True):
        st.markdown(f"**受験者**: {target.get('staff', '')}")
        st.markdown(f"**ブランド**: {target.get('brand_ja','')} / {target.get('brand_en','')}")
        st.markdown(f"**品名**: {target.get('product_name', '')}")
        st.markdown(f"**製造年**: {target.get('year', '')}")
        st.markdown(f"**付属品**: {target.get('accessories', '')}")
        st.markdown(f"**暫定rank**: {target.get('rank', '')}")
        pmin = target.get("price_min_usd", "")
        pmax = target.get("price_max_usd", "")
        if pmin and pmax:
            st.markdown(f"**相場メモ**: ${pmin} 〜 ${pmax}")
        st.markdown(f"**🟦 staff の買取金額**: **${target.get('staff_offer_price', '')}**")

        # v0.13.1 (項目4): 原価率を自動表示(買取額÷相場上限 〜 買取額÷相場下限)
        try:
            _offer = float(target.get("staff_offer_price", 0) or 0)
            _pmin = float(pmin or 0)
            _pmax = float(pmax or 0)
        except (ValueError, TypeError):
            _offer = _pmin = _pmax = 0.0
        if _offer > 0 and _pmin > 0 and _pmax > 0:
            _lo_rate = _offer / max(_pmin, _pmax) * 100  # 上限で割る=低い率
            _hi_rate = _offer / min(_pmin, _pmax) * 100  # 下限で割る=高い率
            st.markdown(f"**📊 原価率**: 約 {_lo_rate:.0f}〜{_hi_rate:.0f}%")

    # 画像2系統: screenshot_ids = "ts::market|ts::item"
    raw_ids = str(target.get("screenshot_ids", "") or "").strip()
    market_id, item_id = "", ""
    if "|" in raw_ids:
        parts = raw_ids.split("|", 1)
        market_id = parts[0].strip()
        item_id = parts[1].strip() if len(parts) > 1 else ""
    elif raw_ids:
        # 旧形式の保険(単一ID)。商品画像扱いにする。
        item_id = raw_ids

    with st.container(border=True):
        _show_shot_group(item_id, "🖼️ 商品画像(全体 + 査定ポイント)",
                         key_prefix=f"item_{target_idx}", point_label_overall=True)
    with st.container(border=True):
        _show_shot_group(market_id, "📊 相場参考スクショ",
                         key_prefix=f"market_{target_idx}", point_label_overall=False)

    # --- 4軸評価フォーム ---
    st.markdown(t("ui.training_review.expert_header"))
    # v0.13.1: 2択(適切/要改善)→ 3段階(適切 / 少し改善 / 要改善)
    _EVAL_CHOICES = ["適切", "少し改善", "要改善"]
    with st.form(f"train_review_form_{target_idx}"):
        eval_input = st.radio(t("ui.training_review.axis1"), _EVAL_CHOICES, horizontal=True, key=f"tr_ax1_{target_idx}")
        eval_market = st.radio(t("ui.training_review.axis2"), _EVAL_CHOICES, horizontal=True, key=f"tr_ax2_{target_idx}")
        eval_rank = st.radio(t("ui.training_review.axis3"), _EVAL_CHOICES, horizontal=True, key=f"tr_ax3_{target_idx}")

        st.markdown("**" + t("ui.training_review.axis4") + "**")
        try:
            _staff_offer_val = float(target.get("staff_offer_price", 0) or 0)
        except (ValueError, TypeError):
            _staff_offer_val = 0.0
        st.caption(f"staff の買取金額: ${_staff_offer_val:.0f}")
        _ep1, _ep2 = st.columns(2)
        with _ep1:
            expert_min = st.number_input(
                t("ui.training_review.expert_price_min"), min_value=0, step=1, format="%d",
                key=f"tr_emin_{target_idx}",
                help=t("ui.training_review.min_help"))
        with _ep2:
            expert_max = st.number_input(
                t("ui.training_review.expert_price_max"), min_value=0, step=1, format="%d",
                key=f"tr_emax_{target_idx}",
                help=t("ui.training_review.max_help"))

        st.markdown("**" + t("ui.training_review.mark") + "**")
        _MARKS = {
            t("ui.training_review.mark.hanamaru"): "hanamaru",
            t("ui.training_review.mark.yoku"): "yoku",
            t("ui.training_review.mark.ganbaro"): "ganbaro",
        }
        mark_label = st.radio(t("ui.training_review.mark"), list(_MARKS.keys()), horizontal=True,
                              key=f"tr_mark_{target_idx}", label_visibility="collapsed")

        eval_comment = st.text_area(
            t("ui.training_review.comment"), height=100,
            placeholder=t("ui.training.comment_placeholder"))

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            save_btn = st.form_submit_button(t("ui.training_review.save"), type="primary", use_container_width=True)
        with col_b2:
            skip_btn = st.form_submit_button(t("ui.training.skip"), use_container_width=True)

        if save_btn:
            # ズレ計算: staff額がレンジ[min,max]内なら0、外れていれば最寄り境界からの差
            gap = ""
            if expert_min > 0 and expert_max > 0 and _staff_offer_val > 0:
                lo, hi = min(expert_min, expert_max), max(expert_min, expert_max)
                if _staff_offer_val < lo:
                    gap = int(_staff_offer_val - lo)   # 負: 安く見積もりすぎ
                elif _staff_offer_val > hi:
                    gap = int(_staff_offer_val - hi)   # 正: 高く見積もりすぎ
                else:
                    gap = 0                             # レンジ内
            df.at[target_idx, "eval_input"] = eval_input
            df.at[target_idx, "eval_market_image"] = eval_market
            df.at[target_idx, "eval_rank"] = eval_rank
            df.at[target_idx, "expert_answer_min"] = expert_min if expert_min > 0 else ""
            df.at[target_idx, "expert_answer_max"] = expert_max if expert_max > 0 else ""
            df.at[target_idx, "price_gap"] = gap
            df.at[target_idx, "overall_mark"] = _MARKS[mark_label]
            df.at[target_idx, "eval_comment"] = eval_comment
            df.at[target_idx, "review_status"] = "reviewed"
            df.at[target_idx, "reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            be.write_sheet("training_history", df)

            # v0.14.0: 評価された staff 本人に Slack DM 通知(失敗しても保存は成功扱い)
            _staff_name = str(target.get("staff", "")).strip()
            _slack_map = load_staff_slack_map()
            _sid = _slack_map.get(_staff_name, "")
            _brand = target.get("brand_ja", "") or target.get("brand_en", "")
            _item = target.get("product_name", "")
            _result = _MARKS[mark_label]
            _ans = ""
            if expert_min > 0 and expert_max > 0:
                _ans = f"${expert_min}–${expert_max}"
            _dm = (
                "🦉 *Chosuke Training Reviewed!* / ការវាយតម្លៃរបស់អ្នកត្រូវបានពិនិត្យ\n"
                f"• Brand / ម៉ាក: {_brand}\n"
                f"• Item / ផលិតផល: {_item}\n"
                f"• Result / លទ្ធផល: {_result}\n"
            )
            if _ans:
                _dm += f"• Correct range / តម្លៃត្រឹមត្រូវ: {_ans}\n"
            if (eval_comment or "").strip():
                _dm += f"• Comment / មតិ: {eval_comment.strip()}\n"
            _dm += "\nOpen Chosuke → *My Results / លទ្ធផលរបស់ខ្ញុំ* to see details."

            _ok, _why = send_slack_dm(_sid, _dm)
            # 送信結果を session_state に残す(rerun で消えないよう、画面上部に常時表示する)
            st.session_state["last_slack_result"] = {
                "ok": _ok,
                "why": _why,
                "staff": _staff_name,
                "slack_id": _sid,
                "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dm": _dm,
            }
            st.rerun()

        if skip_btn:
            df.at[target_idx, "review_status"] = "skipped"
            df.at[target_idx, "reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            be.write_sheet("training_history", df)
            st.info(t("ui.training_review.skipped"))
            st.rerun()


def settings_mode():
    st.markdown("## ⚙️ " + t("ui.mode.settings"))

    st.markdown(t("ui.settings.storage_header"))
    st.caption(t("ui.settings.storage_caption"))

    try:
        _sid = st.secrets.get("spreadsheet_id", "(未設定)")
    except Exception:
        _sid = "(secrets 未設定)"
    st.markdown(f"**スプレッドシートID**: `{_sid}`")
    st.caption(t("ui.settings.screenshot_caption"))

    st.markdown(t("ui.settings.rowcounts"))
    try:
        for _name in ["brands", "checklists", "feedback",
                      "appraisal_history", "keyword_requirements", "staff_master",
                      "screenshots"]:
            _df = be.read_sheet(_name)
            st.text(f"  📄 {_name}  ({len(_df)} 行)")
    except Exception as e:
        st.warning(f"タブ情報の取得に失敗しました: {e}")

    # staff マスタ管理(管理者のみ)
    st.markdown("---")
    st.markdown(t("ui.settings.staff_header"))
    st.caption(t("ui.settings.staff_caption"))
    _roster = load_staff_master()
    st.text("現在の名簿: " + ", ".join(_roster))
    _new_staff = st.text_input(t("ui.settings.staff_add_label"), placeholder=t("ui.settings.staff_placeholder"), key="settings_new_staff")
    if st.button(t("ui.settings.staff_add_btn")):
        _ns = (_new_staff or "").strip()
        if _ns:
            add_staff_to_master(_ns)
            st.success(f"追加しました: {_ns}")
            st.rerun()
        else:
            st.warning(t("ui.settings.need_name"))

    # v0.14.0: staff の Slack ユーザーID 登録(評価通知DMの宛先)
    st.markdown("---")
    st.markdown("### 🔔 Slack通知の宛先設定")
    st.caption(
        "各staffのSlackユーザーID(U…)を登録すると、トレーニング評価を保存したときに本人へDMが届きます。"
        "\nIDの取り方: Slackで対象者のプロフィール →「⋮」→「Copy member ID」(Uで始まる文字列)"
    )
    try:
        _has_token = bool(st.secrets.get("SLACK_BOT_TOKEN", ""))
    except Exception:
        _has_token = False
    if _has_token:
        st.caption("✅ SLACK_BOT_TOKEN は設定済みです")
    else:
        st.caption("⚠️ SLACK_BOT_TOKEN が未設定です(Streamlitの Settings → Secrets に登録してください)")

    _slack_map = load_staff_slack_map()
    for _nm in _roster:
        _cur = _slack_map.get(_nm, "")
        _c1, _c2 = st.columns([2, 3])
        with _c1:
            st.text(_nm + (" ✅" if _cur else " —"))
        with _c2:
            _val = st.text_input(
                f"Slack ID ({_nm})", value=_cur, key=f"slackid_{_nm}",
                placeholder="U01ABC2DEF", label_visibility="collapsed")
        if _val.strip() != _cur:
            set_staff_slack_id(_nm, _val.strip())
            st.toast(f"{_nm} のSlack IDを更新しました")

    st.markdown("---")
    st.markdown(t("ui.settings.api_header"))
    st.info(
        "現在はAPIなし(ナレッジベース版)で動作しています。\n\n"
        "Claude APIを接続すると、スクショから自動で相場を推測したり、"
        "商品ごとに動的な確認事項を生成できるようになります。\n\n"
        "API連携を希望する場合は、開発担当に相談してください。"
    )


# ============================================================
# ログインゲート(2区分: staff / 管理者)
# ============================================================
def _check_password(role: str, entered: str) -> bool:
    """Secrets のパスワードと照合する。"""
    try:
        if role == "staff":
            return entered == st.secrets["staff_password"]
        if role == "admin":
            return entered == st.secrets["admin_password"]
    except Exception:
        return False
    return False


def _session_secret() -> str:
    """トークン署名用の秘密鍵。secrets にあれば使い、無ければパスワードから導出する。"""
    try:
        s = st.secrets.get("session_secret", "")
        if s:
            return str(s)
    except Exception:
        pass
    # フォールバック: admin/staff パスワードを連結したものを鍵にする
    try:
        return str(st.secrets.get("admin_password", "")) + "|" + str(st.secrets.get("staff_password", ""))
    except Exception:
        return "chosuke-fallback-secret"


def _make_auth_token(role: str) -> str:
    """role に対する改ざん不可能なトークンを作る(HMAC-SHA256)。"""
    import hashlib, hmac
    msg = f"chosuke-auth:{role}".encode("utf-8")
    key = _session_secret().encode("utf-8")
    sig = hmac.new(key, msg, hashlib.sha256).hexdigest()[:32]
    return f"{role}.{sig}"


def _verify_auth_token(token: str):
    """トークンを検証し、正しければ role を返す。不正なら None。"""
    import hashlib, hmac
    if not token or "." not in token:
        return None
    role, _, sig = token.partition(".")
    if role not in ("staff", "admin"):
        return None
    expected = _make_auth_token(role)
    # 定数時間比較
    if hmac.compare_digest(token, expected):
        return role
    return None


def _persist_login(role: str):
    """ログイン状態を URL クエリパラメータに保存する(セッション切れ対策)。"""
    try:
        st.query_params["auth"] = _make_auth_token(role)
    except Exception:
        pass


def _restore_login_from_url() -> bool:
    """URL のトークンから session_state を復元する。復元できたら True。"""
    if st.session_state.get("authed"):
        return True
    try:
        token = st.query_params.get("auth", "")
    except Exception:
        token = ""
    role = _verify_auth_token(token)
    if role:
        st.session_state["authed"] = True
        st.session_state["role"] = role
        return True
    return False


def _clear_persisted_login():
    """URL クエリパラメータのログイン状態を消す。"""
    try:
        if "auth" in st.query_params:
            del st.query_params["auth"]
    except Exception:
        pass


def login_gate() -> bool:
    """未ログインならログイン画面を出し、False を返す。
    ログイン済みなら True。staff / admin の2区分。英語併記。"""
    # セッション切れ対策: session_state が空でも URL トークンから復元する
    if _restore_login_from_url():
        return True

    render_header()

    # 区分選択(まだ選んでいなければ2ボタンを出す)
    chosen = st.session_state.get("login_role_choice")
    if not chosen:
        st.markdown(t("ui.login.header"))
        st.caption(t("ui.login.select"))
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("ui.login.staff"), use_container_width=True):
                st.session_state["login_role_choice"] = "staff"
                st.rerun()
        with c2:
            if st.button(t("ui.login.admin"), use_container_width=True):
                st.session_state["login_role_choice"] = "admin"
                st.rerun()
        return False

    # パスワード入力
    role = chosen
    role_label = t("ui.login.status_staff") if role == "staff" else t("ui.login.status_admin")
    st.markdown(f"#### {role_label} " + t("ui.login.button"))
    pw = st.text_input(t("ui.login.password"), type="password", key="login_pw")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button(t("ui.login.button"), type="primary", use_container_width=True):
            if _check_password(role, pw):
                st.session_state["authed"] = True
                st.session_state["role"] = role
                st.session_state.pop("login_role_choice", None)
                st.session_state.pop("login_pw", None)
                _persist_login(role)   # セッション切れでも復元できるよう URL に保存
                st.rerun()
            else:
                st.error(t("ui.login.incorrect"))
    with c2:
        if st.button(t("ui.login.back"), use_container_width=True):
            st.session_state.pop("login_role_choice", None)
            st.rerun()
    return False


# ============================================================
# メイン
# ============================================================
def main():
    st.set_page_config(
        page_title="Chosuke - Eco Ring Cambodia",
        page_icon="🦉",
        layout="wide",
    )

    inject_css()

    # --- ログインゲート(未ログインならここで止める) ---
    if not login_gate():
        return

    init_data()
    render_header()

    role = st.session_state.get("role", "staff")
    is_admin = role == "admin"

    # ロール別に使えるモードを決める。
    # staff: 査定モードのみ。 admin: 全モード。
    if is_admin:
        mode_keys = ["🔍 査定モード", "📝 査定レビューモード", "🎓 トレーニング評価モード",
                     "📚 ナレッジ管理モード", "⚙️ 設定"]
    else:
        mode_keys = ["🔍 査定モード", "🎓 トレーニングモード"]

    with st.sidebar:
        st.markdown(t("ui.sidebar.mode_select"))
        _MODE_LABEL = {
            "🔍 査定モード": "ui.mode.appraisal",
            "📝 査定レビューモード": "ui.mode.review",
            "🎓 トレーニングモード": "ui.mode.training",
            "🎓 トレーニング評価モード": "ui.mode.training_review",
            "📚 ナレッジ管理モード": "ui.mode.knowledge",
            "⚙️ 設定": "ui.mode.settings",
        }
        _MODE_EMOJI = {
            "🔍 査定モード": "🔍",
            "📝 査定レビューモード": "📝",
            "🎓 トレーニングモード": "🎓",
            "🎓 トレーニング評価モード": "🎓",
            "📚 ナレッジ管理モード": "📚",
            "⚙️ 設定": "⚙️",
        }
        if is_admin:
            mode = st.radio(
                "操作モード",
                mode_keys,
                format_func=lambda v: f"{_MODE_EMOJI.get(v,'')} {t(_MODE_LABEL.get(v, v))}".strip(),
                label_visibility="collapsed"
            )
        else:
            # staff: 査定モード + トレーニングモードから選択
            mode = st.radio(
                "操作モード",
                mode_keys,
                format_func=lambda v: f"{_MODE_EMOJI.get(v,'')} {t(_MODE_LABEL.get(v, v))}".strip(),
                label_visibility="collapsed"
            )

        st.markdown("---")
        lang_label = {"ja": "🇯🇵 日本語", "en": "🇬🇧 English", "km": "🇰🇭 ភាសាខ្មែរ"}
        lang_options = ["ja", "en", "km"]
        _cur = st.session_state.get("lang", "ja")
        current_idx = lang_options.index(_cur) if _cur in lang_options else 0
        chosen_lang = st.radio(
            "Language / ភាសា",
            lang_options,
            index=current_idx,
            format_func=lambda x: lang_label[x],
            key="lang_selector",
            horizontal=True,
        )
        if chosen_lang != st.session_state.get("lang"):
            st.session_state.lang = chosen_lang
            st.rerun()
        if st.session_state.lang in ("en", "km"):
            st.caption(t("ui.sidebar.partial_translation"))

        st.markdown("---")
        _role_disp = t("ui.login.status_admin") if is_admin else t("ui.login.status_staff")
        st.caption(t("ui.sidebar.logged_in", role=_role_disp))
        if st.button(t("ui.logout"), use_container_width=True):
            for k in ["authed", "role", "login_role_choice"]:
                st.session_state.pop(k, None)
            _clear_persisted_login()   # URL のログイントークンも消す
            st.rerun()

        st.markdown("---")
        st.markdown("**Chosuke v0.14.0 (cloud)**")
        st.caption("Wise eyes never miss a corner.")

    # ロール外モードへの直接アクセスを防ぐ(保険)
    if mode not in mode_keys:
        mode = "🔍 査定モード"

    if mode == "🔍 査定モード":
        appraisal_mode()
    elif mode == "📝 査定レビューモード":
        review_mode()
    elif mode == "🎓 トレーニングモード":
        training_mode()
    elif mode == "🎓 トレーニング評価モード":
        training_review_mode()
    elif mode == "📚 ナレッジ管理モード":
        knowledge_mode()
    else:
        settings_mode()

    st.markdown(f"""
    <div class="chosuke-footer">
        Chosuke v0.14.0 🦉 · Eco Ring Cambodia AI Appraisal Assistant<br>
        {t("ui.footer.tagline")}
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
