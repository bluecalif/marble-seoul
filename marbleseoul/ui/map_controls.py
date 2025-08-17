import streamlit as st


def render_map_controls(state, price_quintiles):
    """지도 제어 UI를 렌더링하고, 사용자 액션을 반환합니다."""
    st.markdown("##### 🗺️ 지도 표시 구간 선택")
    st.write("관심 있는 아파트 가격대를 선택하면 해당 지역이 지도에 표시됩니다.")

    selected_action = None
    cols = st.columns(6)
    quintile_labels = {
        1: "상위 20%",
        2: "중상위 20%",
        3: "중위 20%",
        4: "중하위 20%",
        5: "하위 20%",
    }

    for i in range(5):
        quintile = i + 1
        with cols[i]:
            quintile_info = price_quintiles.get(quintile, {})
            price_min = quintile_info.get("price_min", 0)
            price_max = quintile_info.get("price_max", 0)
            button_key = f"quintile_button_{quintile}"

            if st.button(
                f"{quintile_labels[quintile]}",
                help=f"{price_min:,.0f}만원 ~ {price_max:,.0f}만원",
                key=button_key,
            ):
                selected_action = {"type": "select_quintile", "data": quintile}

    with cols[5]:
        if st.button("전체", help="모든 자치구를 표시합니다.", key="quintile_reset"):
            selected_action = {"type": "select_quintile", "data": None}

    return selected_action
