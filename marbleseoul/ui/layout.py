import streamlit as st


def configure_page():
    """
    Streamlit 페이지의 기본 설정을 구성합니다.
    - 페이지 설정 (wide layout)
    - 독립 스크롤을 위한 CSS 스타일링
    """
    st.set_page_config(page_title="Marble서울 Prototype", layout="wide")

    # 독립 스크롤 및 UI 개선을 위한 간소화된 CSS
    st.markdown(
        """
    <style>
    /* 기본 페이지 설정 */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* 랭킹 테이블 스타일링 */
    .ranking-table-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    /* 버튼 스타일 개선 */
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #d1d5db;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 데이터프레임 스타일링 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }
    
    /* 컬럼 구분선 */
    div[data-testid="column"]:first-child {
        border-right: 2px solid #e0e0e0;
        padding-right: 1rem;
    }
    
    div[data-testid="column"]:last-child {
        padding-left: 1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
