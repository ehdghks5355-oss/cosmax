import pathlib
import streamlit as st
import streamlit.components.v1 as components

# ── 기본 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="INCIscope — 전성분 분석기",
    page_icon="🧴",
    layout="wide",
)

# Streamlit 기본 여백/헤더를 최소화해서 HTML 앱이 화면을 꽉 채우도록 함
st.markdown(
    """
    <style>
        .block-container {padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem; max-width: 100%;}
        header {visibility: hidden;}
        iframe {display: block;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── index.html 로드 ──────────────────────────────────────────
HTML_PATH = pathlib.Path(__file__).parent / "index.html"
html_content = HTML_PATH.read_text(encoding="utf-8")

# 이 앱은 순수 클라이언트 사이드(HTML/CSS/JS)로 동작하며 서버 호출이 없으므로
# components.html로 그대로 임베드합니다.
components.html(html_content, height=1400, scrolling=True)
