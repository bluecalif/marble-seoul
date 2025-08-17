# marble/marbleseoul/ui/chat_interface.py
import streamlit as st

from ..utils import constants as const
from ..utils import formatters as fmt
from ..app import langchain_chat as lc


def render_chat_interface(state, latest_month, latest_avg_price, gugun_ranking_df):
    """챗봇 UI를 렌더링하고 사용자 액션을 반환합니다."""
    st.subheader("챗봇 (베타)")
    user_action = None
    selected_gugun = None

    # --- 랭킹 테이블 표시 (접기/펼치기 기능 포함) ---
    if st.session_state.get("ranking_df") is not None:
        # CSS 클래스를 적용한 컨테이너로 감싸기
        st.markdown('<div class="ranking-table-container">', unsafe_allow_html=True)

        # 접기/펼치기 상태 초기화
        if "ranking_table_expanded" not in st.session_state:
            st.session_state.ranking_table_expanded = True

        # 헤더와 토글 버튼
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("##### 🏆 자치구별 매매가 랭킹 (84m² 기준)")
        with col2:
            if st.button(
                "📋" if st.session_state.ranking_table_expanded else "📊",
                help="랭킹 테이블 접기/펼치기",
                key="toggle_ranking_table",
            ):
                st.session_state.ranking_table_expanded = (
                    not st.session_state.ranking_table_expanded
                )
                st.rerun()

        # 테이블 표시 (확장 상태일 때만)
        if st.session_state.ranking_table_expanded:
            st.dataframe(st.session_state.ranking_df, use_container_width=True)
            st.caption(
                "💡 이 테이블은 대화 중에도 계속 표시됩니다. 우측 버튼으로 접을 수 있습니다."
            )
        else:
            st.info("📊 랭킹 테이블이 접혀있습니다. 우측 버튼을 클릭하여 펼치세요.")

        # 랭킹 테이블 컨테이너 닫기
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 자치구 선택 UI 제거 (main.py에서 처리) ---
    # 중복 제거: main.py에 자치구 재선택 풀다운이 있으므로 여기서는 제거

    # --- 채팅 기록 표시 (독립 스크롤 컨테이너) ---
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    # --- 사용자 입력 처리 ---
    print("🚨🚨🚨 CHAT_INTERFACE: CHECKING FOR USER INPUT 🚨🚨🚨")
    user_action = None  # 기본값 설정
    
    if user_input := st.chat_input("메시지를 입력하세요…"):
        print(f"🚨🚨🚨 CHAT_INTERFACE: USER INPUT DETECTED: {user_input} 🚨🚨🚨")
        if any(keyword in user_input for keyword in const.RANKING_KEYWORDS):
            user_action = {"type": "show_ranking", "data": user_input}
            print(f"🚨 ACTION TYPE: show_ranking")
        elif any(keyword in user_input for keyword in const.RESET_KEYWORDS):
            user_action = {"type": "reset_view", "data": user_input}
            print(f"🚨 ACTION TYPE: reset_view")
        else:
            # 일반 채팅
            user_action = {"type": "chat", "data": user_input}
            print(f"🚨 ACTION TYPE: chat")
        print(f"🚨🚨🚨 CHAT_INTERFACE: RETURNING ACTION: {user_action} 🚨🚨🚨")
    else:
        print("🚨🚨🚨 CHAT_INTERFACE: NO USER INPUT - RETURNING None 🚨🚨🚨")

    return user_action
