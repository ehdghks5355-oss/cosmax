from __future__ import annotations

import html
import re
from urllib.parse import quote

import altair as alt
import pandas as pd
import streamlit as st

# ── 기본 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="INCIscope — 전성분 분석기",
    page_icon="🧪",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; max-width: 960px;}
        .trend-badge {
            display: inline-block;
            background: #fdf1e4;
            color: #d9822b;
            border: 1px solid #f2d9b8;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin: 2px 4px 2px 0;
        }
        .ingredient-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        .ingredient-table th, .ingredient-table td {
            text-align: left;
            padding: 6px 8px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.25);
        }
        .ingredient-table th {
            font-weight: 600;
        }
        .func-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12.5px;
            font-weight: 600;
            white-space: nowrap;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 공개된 INCI 기능 분류만 사용 (자사 원료 DB 미사용) — 성분명 → (기능 분류, 트렌드 여부)
INGREDIENT_DB = {
    "정제수": ("기타(베이스)", False),
    "글리세린": ("보습제", False),
    "부틸렌글라이콜": ("보습제", False),
    "나이아신아마이드": ("활성성분", True),
    "1,2-헥산다이올": ("방부", False),
    "세테아릴알코올": ("점증/유화", False),
    "다이메티콘": ("필름형성제", False),
    "카보머": ("점증/유화", False),
    "알란토인": ("활성성분", False),
    "병풀추출물": ("활성성분", True),
    "병풀잎수": ("활성성분", True),
    "페녹시에탄올": ("방부", False),
    "향료": ("기타(베이스)", False),
    # 메이크업 — 베이스
    "싸이클로펜타실록세인": ("오일/휘발성베이스", False),
    "탈크": ("파우더/분체", False),
    "티타늄디옥사이드": ("안료/컬러런트", False),
    "마이카": ("펄/광택제", False),
    "나일론-12": ("필름형성제", False),
    "적색산화철": ("안료/컬러런트", False),
    "황색산화철": ("안료/컬러런트", False),
    "세틸피이지/피피지-10/1디메티콘": ("점증/유화", False),
    "토코페롤": ("활성성분", True),
    # 메이크업 — 색조
    "카나우바왁스": ("오일/왁스(베이스)", True),
    "칸데릴라왁스": ("오일/왁스(베이스)", False),
    "폴리부텐": ("점증/유화", False),
    "적색227호": ("안료/컬러런트", False),
    # 실제 전성분표에서 자주 등장하는 스킨케어 활성/보습/베이스 성분
    "다이부틸아디페이트": ("오일/에몰리언트", False),
    "카프릴릭/카프릭트라이글리세라이드": ("오일/에몰리언트", False),
    "하이드로제네이티드레시틴": ("점증/유화", False),
    "암모늄아크릴로일다이메틸타우레이트/브이피코폴리머": ("점증/유화", False),
    "콜레스테롤": ("보습제", False),
    "돌콩오일": ("오일/에몰리언트", False),
    "에틸헥실글리세린": ("방부", False),
    "토코페릴아세테이트": ("활성성분", False),
    "소듐메틸스테아로일타우레이트": ("점증/유화", False),
    "해바라기씨오일": ("오일/에몰리언트", False),
    "폴리글리세릴-6카프릴레이트": ("점증/유화", False),
    "다이메틸아이소소바이드": ("pH조절/가용화", False),
    "아데노신": ("활성성분", True),
    "레티놀": ("활성성분", True),
    "당근추출물": ("활성성분", False),
    "잔탄검": ("점증/유화", False),
    "폴리글리세릴-10라우레이트": ("점증/유화", False),
    "하이드록시피나콜론레티노에이트": ("활성성분", True),
    "레틴알": ("활성성분", True),
    "풀루란": ("필름형성제", False),
    "세라마이드엔피": ("활성성분", True),
    "하이알루로닉애씨드": ("보습제", True),
    "베타-카로틴": ("활성성분", False),
    "트로메타민": ("pH조절/가용화", False),
    "시트릭애씨드": ("pH조절/가용화", False),
    "소듐시트레이트": ("pH조절/가용화", False),
    "글라이코프로테인": ("활성성분", False),
    # 활성성분 — 장벽/진정/미백/각질 케어
    "스핑고리피드": ("활성성분", True),
    "세라마이드": ("활성성분", True),
    "세라마이드3": ("활성성분", True),
    "아스코빅애씨드": ("활성성분", False),
    "아스코빌글루코사이드": ("활성성분", False),
    "마그네슘아스코빌포스페이트": ("활성성분", False),
    "레스베라트롤": ("활성성분", False),
    "판테놀": ("활성성분", True),
    "베타글루칸": ("활성성분", False),
    "아젤라익애씨드": ("활성성분", True),
    "살리실릭애씨드": ("활성성분", False),
    "글라이콜릭애씨드": ("활성성분", False),
    "락틱애씨드": ("활성성분", False),
    "만델릭애씨드": ("활성성분", False),
    "트라넥사믹애씨드": ("활성성분", True),
    "알부틴": ("활성성분", False),
    "유비퀴논": ("활성성분", False),
    "녹차추출물": ("활성성분", False),
    "어성초추출물": ("활성성분", False),
    "프로폴리스추출물": ("활성성분", False),
    "마데카소사이드": ("활성성분", True),
    "마데카식애씨드": ("활성성분", False),
    "아시아티코사이드": ("활성성분", False),
    "비오틴": ("활성성분", False),
    "판테닐트라이아세테이트": ("활성성분", False),
    # 보습제
    "소듐하이알루로네이트": ("보습제", True),
    "하이드롤라이즈드하이알루로닉애씨드": ("보습제", True),
    "하이드롤라이즈드소듐하이알루로네이트": ("보습제", True),
    "소듐피씨에이": ("보습제", False),
    "유레아": ("보습제", False),
    "베타인": ("보습제", False),
    "트레할로스": ("보습제", False),
    "프로판다이올": ("보습제", False),
    "다이프로필렌글라이콜": ("보습제", False),
    "폴리글루탐산": ("보습제", False),
    # 점증/유화
    "하이드록시에틸셀룰로오스": ("점증/유화", False),
    "아크릴레이트/C10-30알킬아크릴레이트크로스폴리머": ("점증/유화", False),
    "다이스테아다이모늄헥토라이트": ("점증/유화", False),
    "피이지-100스테아레이트": ("점증/유화", False),
    "글리세릴스테아레이트": ("점증/유화", False),
    "소르비탄올리에이트": ("점증/유화", False),
    "폴리소르베이트20": ("점증/유화", False),
    "폴리소르베이트60": ("점증/유화", False),
    "폴리소르베이트80": ("점증/유화", False),
    "스테아레스-21": ("점증/유화", False),
    # 방부/방부보조/킬레이트
    "클로르페네신": ("방부", False),
    "소듐벤조에이트": ("방부", False),
    "포타슘소르베이트": ("방부", False),
    "벤질알코올": ("방부", False),
    "다이소듐이디티에이": ("방부", False),
    "이디티에이": ("방부", False),
    # 계면활성제/세정성분 (클렌징)
    "소듐라우레스설페이트": ("계면활성제", False),
    "코카미도프로필베타인": ("계면활성제", False),
    "소듐코코일글루타메이트": ("계면활성제", True),
    "디소듐코코암포디아세테이트": ("계면활성제", False),
    "라우릴글루코사이드": ("계면활성제", False),
    "데실글루코사이드": ("계면활성제", False),
    # 자외선차단 (선케어)
    "에틸헥실메톡시신나메이트": ("자외선차단", False),
    "호모살레이트": ("자외선차단", False),
    "옥토크릴렌": ("자외선차단", False),
    "징크옥사이드": ("자외선차단", True),
    "다이에틸아미노하이드록시벤조일헥실벤조에이트": ("자외선차단", False),
    "비스에틸헥실옥시페놀메톡시페닐트라이아진": ("자외선차단", False),
    # 헤어케어
    "세트리모늄클로라이드": ("컨디셔닝제", False),
    "다이메티코놀": ("컨디셔닝제", False),
    "하이드롤라이즈드케라틴": ("활성성분", False),
    "아르기닌": ("pH조절/가용화", False),
    "알지닌": ("pH조절/가용화", False),
    "멘톨": ("기타(베이스)", False),
    "폴리쿼터늄-10": ("컨디셔닝제", False),
    "폴리쿼터늄-7": ("컨디셔닝제", False),
    "스테아트리모늄클로라이드": ("컨디셔닝제", False),
    "다이스테아릴다이모늄클로라이드": ("점증/유화", False),
    # 활성성분 — 펩타이드/발효/한국 트렌드 성분
    "팔미토일펜타펩타이드-4": ("활성성분", True),
    "아세틸헥사펩타이드-8": ("활성성분", True),
    "카퍼트라이펩타이드-1": ("활성성분", True),
    "아스타잔틴": ("활성성분", True),
    "우렁이점액필터레이트": ("활성성분", True),
    "비피다발효용해물": ("활성성분", True),
    "갈락토미세스발효여과물": ("활성성분", True),
    "콜라겐": ("활성성분", False),
    "카모마일꽃추출물": ("활성성분", False),
    "티트리잎오일": ("활성성분", False),
    "로즈마리잎추출물": ("활성성분", False),
    "알로에베라잎추출물": ("활성성분", False),
    "인삼뿌리추출물": ("활성성분", False),
    "히비스커스꽃추출물": ("활성성분", False),
    "폴리감마글루탐산": ("보습제", False),
    # 오일/에몰리언트 — 추가 오일류
    "호호바오일": ("오일/에몰리언트", False),
    "스쿠알란": ("오일/에몰리언트", True),
    "마카다미아씨오일": ("오일/에몰리언트", False),
    "아르간오일": ("오일/에몰리언트", False),
    "시어버터": ("오일/에몰리언트", False),
    "사이클로헥사실록세인": ("오일/휘발성베이스", False),
    "페닐트라이메티콘": ("오일/에몰리언트", False),
    "카프릴릴메티콘": ("오일/에몰리언트", False),
    # 계면활성제 추가
    "소듐라우로일사코시네이트": ("계면활성제", False),
    "라우라마이드디이에이": ("계면활성제", False),
    # PEG계 유화제
    "피이지-6카프릴릭/카프릭글리세라이즈": ("점증/유화", False),
    "피이지-4카프릴릭/카프릭글리세라이즈": ("점증/유화", False),
    "피이지-60글리세릴스테아레이트": ("점증/유화", False),
    "피이지-6코카마이드포스페이트": ("계면활성제", False),
    # 방부 추가
    "클로로자이레놀": ("방부", False),
    "소듐데하이드로아세테이트": ("방부", False),
    # 기타 확인 후 추가
    "하이드로제네이티드쌀겨오일": ("오일/에몰리언트", False),
    "폴리글리세릴-3메틸글루코오스다이스테아레이트": ("점증/유화", False),
    "폴리아크릴레이트크로스폴리머-6": ("점증/유화", False),
    "만니톨": ("보습제", False),
    "카프릴하이드록사믹애씨드": ("방부", False),
    # 자외선차단 추가
    "이소아밀p-메톡시신나메이트": ("자외선차단", False),
    "다이에틸헥실부타미도트리아존": ("자외선차단", False),
    # 보습/텍스처 추가
    "솔비톨": ("보습제", False),
    "말토덱스트린": ("점증/유화", False),
    # 지방알코올/에스터 계열 점증·유화 보조제
    "폴리글리세릴-2스테아레이트": ("점증/유화", False),
    "아라키딜알코올": ("점증/유화", False),
    "스테아릴알코올": ("점증/유화", False),
    "베헤닐알코올": ("점증/유화", False),
    "C12-16알코올": ("점증/유화", False),
    "아라키딜글루코사이드": ("점증/유화", False),
    "팔미틱애씨드": ("점증/유화", False),
    "다이메티콘/비닐다이메티콘크로스폴리머": ("필름형성제", False),
    # 보습제 추가 (하이알루로닉애씨드 유도체 등)
    "글리세릴글루코사이드": ("보습제", False),
    "글루코오스": ("보습제", False),
    "다이메틸실란올하이알루로네이트": ("보습제", True),
    "포타슘하이알루로네이트": ("보습제", True),
    "소듐하이알루로네이트크로스폴리머": ("보습제", True),
    "하이드록시프로필트라이모늄하이알루로네이트": ("보습제", True),
    "소듐하이알루로네이트다이메틸실란올": ("보습제", True),
    "소듐아세틸레이티드하이알루로네이트": ("보습제", True),
    # 오일/에몰리언트 추가
    "C13-15알케인": ("오일/에몰리언트", False),
    # 방부/킬레이트 추가
    "에티드론산": ("방부", False),
    # 활성성분 — 산화방지/추출물/발효/펩타이드 추가
    "펜타에리스리틸테트라-다이-t-부틸하이드록시하이드로신나메이트": ("활성성분", False),
    "로즈마리추출물": ("활성성분", False),
    "락토바실러스발효용해물": ("활성성분", True),
    "마트리카리아꽃오일": ("활성성분", False),
    "소양삼추출물": ("활성성분", True),
    "소듐디엔에이": ("활성성분", True),
    "트라이펩타이드-1": ("활성성분", True),
    "아세틸테트라펩타이드-5": ("활성성분", True),
    "팔미토일트라이펩타이드-1": ("활성성분", True),
    "헥사펩타이드-11": ("활성성분", True),
    "헥사펩타이드-9": ("활성성분", True),
    "팔미토일트라이펩타이드-5": ("활성성분", True),
}

# 기능 분류 색상 — palette.md의 검증된 8개 카테고리 색상(파랑/아쿠아/노랑/초록/
# 보라/빨강/마젠타/오렌지)에 유사 기능군을 매핑하고, '기타(베이스)'는 중성색,
# '미분류'는 상태색(경고, 항상 아이콘+라벨 동반)을 사용한다.
# 값 형식: (라이트 배경, 라이트 글자색, 다크 배경, 다크 글자색)
FUNC_STYLE: dict[str, tuple[str, str, str, str]] = {
    "보습제": ("#2a78d6", "#ffffff", "#3987e5", "#ffffff"),
    "계면활성제": ("#1baf7a", "#ffffff", "#199e70", "#ffffff"),
    "컨디셔닝제": ("#1baf7a", "#ffffff", "#199e70", "#ffffff"),
    "방부": ("#eda100", "#1a1a19", "#c98500", "#1a1a19"),
    "pH조절/가용화": ("#eda100", "#1a1a19", "#c98500", "#1a1a19"),
    "점증/유화": ("#008300", "#ffffff", "#008300", "#ffffff"),
    "필름형성제": ("#008300", "#ffffff", "#008300", "#ffffff"),
    "활성성분": ("#4a3aa7", "#ffffff", "#9085e9", "#1a1a19"),
    "자외선차단": ("#e34948", "#ffffff", "#e66767", "#ffffff"),
    "안료/컬러런트": ("#e87ba4", "#1a1a19", "#d55181", "#ffffff"),
    "펄/광택제": ("#e87ba4", "#1a1a19", "#d55181", "#ffffff"),
    "파우더/분체": ("#e87ba4", "#1a1a19", "#d55181", "#ffffff"),
    "오일/에몰리언트": ("#eb6834", "#ffffff", "#d95926", "#ffffff"),
    "오일/왁스(베이스)": ("#eb6834", "#ffffff", "#d95926", "#ffffff"),
    "오일/휘발성베이스": ("#eb6834", "#ffffff", "#d95926", "#ffffff"),
    "기타(베이스)": ("#e1e0d9", "#52514e", "#2c2c2a", "#c3c2b7"),
    "미분류": ("#fab219", "#1a1a19", "#fab219", "#1a1a19"),
}
FUNC_SLUGS: dict[str, str] = {func: f"func-{idx}" for idx, func in enumerate(FUNC_STYLE)}


def func_badge_css() -> str:
    light_rules = [
        f".func-badge.{FUNC_SLUGS[func]}{{background:{bg_l};color:{fg_l};}}"
        for func, (bg_l, fg_l, _bg_d, _fg_d) in FUNC_STYLE.items()
    ]
    dark_rules = [
        f".func-badge.{FUNC_SLUGS[func]}{{background:{bg_d};color:{fg_d};}}"
        for func, (_bg_l, _fg_l, bg_d, fg_d) in FUNC_STYLE.items()
    ]
    return (
        "\n".join(light_rules)
        + "\n@media (prefers-color-scheme: dark) {\n"
        + "\n".join(dark_rules)
        + "\n}"
    )


def func_badge_html(func: str) -> str:
    slug = FUNC_SLUGS.get(func, FUNC_SLUGS["미분류"])
    icon = "⚠️ " if func == "미분류" else ""
    return f'<span class="func-badge {slug}">{icon}{html.escape(func)}</span>'


st.markdown(f"<style>{func_badge_css()}</style>", unsafe_allow_html=True)


def split_ingredient_text(text: str) -> list[str]:
    """쉼표로 성분을 분리한다. 단, 아래는 성분 구분자로 보지 않는다.
    - 괄호 안의 쉼표 (예: "레티놀(1,000IU/g)")
    - 숫자 사이에 낀 쉼표 (예: "1,2-헥산다이올")
    """
    items = []
    depth = 0
    current = ""
    length = len(text)
    for idx, ch in enumerate(text):
        if ch == "(":
            depth += 1
        if ch == ")":
            depth = max(0, depth - 1)

        between_digits = (
            ch == ","
            and idx > 0
            and idx + 1 < length
            and text[idx - 1].isdigit()
            and text[idx + 1].isdigit()
        )

        if ch == "," and depth == 0 and not between_digits:
            items.append(current.strip())
            current = ""
        else:
            current += ch

    if current.strip():
        items.append(current.strip())

    return [item for item in items if item]


def parse_ingredient_item(raw: str) -> tuple[str, str | None]:
    """"성분명(부가정보)" 형태에서 검색/DB조회에 쓸 순수 성분명과 부가정보를 분리."""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw.strip(), None


def analyze_inci_text(text: str) -> list[dict]:
    """실제 입력된 전성분 텍스트를 파싱해 DB와 매칭 (DB에 없으면 '미분류')."""
    results = []
    for raw in split_ingredient_text(text):
        name, note = parse_ingredient_item(raw)
        entry = INGREDIENT_DB.get(name)
        results.append(
            {
                "name": name,
                "note": note,
                "func": entry[0] if entry else "미분류",
                "trend": entry[1] if entry else False,
                "known": entry is not None,
            }
        )
    return results


def kcia_search_url(name: str) -> str:
    """대한화장품협회(KCIA) 성분사전 검색 딥링크."""
    return "https://kcia.or.kr/cid/search/ingd_list.php?skind=INGD_NM&sword=" + quote(name)


# ── 화면 구성 ─────────────────────────────────────────────
st.title("🧪 INCIscope — 전성분 분석기")
st.caption("전성분을 붙여넣으면, 공개된 성분 기능 분류로 구성과 트렌드를 분석해드립니다")

col_input, col_result = st.columns(2)

with col_input:
    st.subheader("🧴 전성분표 입력")
    raw_input = st.text_area(
        "전성분 (붙여넣기)",
        height=180,
        placeholder=(
            "예) 정제수, 글리세린, 부틸렌글라이콜, 나이아신아마이드, "
            "세테아릴알코올, 다이메티콘, 카보머, 페녹시에탄올 ..."
        ),
    )
    analyze_clicked = st.button("분석하기", type="primary", use_container_width=True)

with col_result:
    st.subheader("📊 분석 결과")

    if not analyze_clicked:
        st.info("전성분표를 입력하고 '분석하기'를 눌러보세요")
    elif not raw_input.strip():
        st.warning("분석할 전성분을 먼저 입력해주세요")
    else:
        ingredients = analyze_inci_text(raw_input)
        total = len(ingredients)

        counts: dict[str, int] = {}
        for i in ingredients:
            counts[i["func"]] = counts.get(i["func"], 0) + 1

        st.markdown(f"**총 {total}개 성분**")

        counts_series = pd.Series(counts).sort_values(ascending=False)
        chart_df = counts_series.rename_axis("기능 분류").reset_index(name="개수")
        func_chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("개수:Q", title="개수"),
                y=alt.Y("기능 분류:N", title=None, sort="-x"),
                color=alt.Color(
                    "기능 분류:N",
                    scale=alt.Scale(
                        domain=list(FUNC_STYLE.keys()),
                        range=[style[0] for style in FUNC_STYLE.values()],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("기능 분류:N", title="기능 분류"),
                    alt.Tooltip("개수:Q", title="개수"),
                ],
            )
        )
        st.altair_chart(func_chart, use_container_width=True)

        trend_items = [i for i in ingredients if i["trend"]]
        st.markdown("**트렌드 활성성분**")
        if trend_items:
            st.markdown(
                "".join(
                    f'<span class="trend-badge">✨ {html.escape(i["name"])}</span>'
                    for i in trend_items
                ),
                unsafe_allow_html=True,
            )
        else:
            st.caption("트렌드 성분 없음")

        rows_html = []
        for i in ingredients:
            display_name = html.escape(
                i["name"] + (f" ({i['note']})" if i["note"] else "")
            )
            db_url = html.escape(kcia_search_url(i["name"]), quote=True)
            rows_html.append(
                "<tr>"
                f"<td>{display_name}</td>"
                f"<td>{func_badge_html(i['func'])}</td>"
                f'<td><a href="{db_url}" target="_blank" rel="noopener">확인 ↗</a></td>'
                "</tr>"
            )
        st.markdown(
            '<table class="ingredient-table">'
            "<thead><tr><th>성분</th><th>기능 분류</th><th>공식 DB</th></tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody>"
            "</table>",
            unsafe_allow_html=True,
        )
        st.caption(
            "※ '확인' 링크는 대한화장품협회 성분사전(kcia.or.kr) 검색 결과를 새 탭에서 엽니다. "
            "'미분류'는 현재 프로토타입 DB에 등록되지 않은 성분입니다."
        )

        top_func, top_count = counts_series.index[0], int(counts_series.iloc[0])
        unknown_count = sum(1 for i in ingredients if not i["known"])

        insights = [
            f"총 {total}개 성분 중 {top_func}가 {top_count}개로 가장 큰 비중을 차지합니다.",
            f"트렌드 성분이 {len(trend_items)}개 포함되어 있습니다"
            + (f" ({', '.join(i['name'] for i in trend_items)})." if trend_items else "."),
            f"방부 성분 개수: {counts.get('방부', 0)}개 — 일반적인 방부 시스템 범위입니다.",
        ]
        if unknown_count:
            insights.append(
                f"DB에 없어 미분류로 표시된 성분이 {unknown_count}개 있습니다 — "
                "'확인' 링크로 공식 DB에서 직접 조회해보세요."
            )

        st.markdown("\n".join(f"- {i}" for i in insights))

st.caption("INCIscope — 화장품 제형 연구원을 위한 성분 트렌드 분석 도우미 (프로토타입)")
