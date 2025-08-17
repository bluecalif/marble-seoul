# marble/marbleseoul/maps/styles.py

SEOUL_TOTAL_STYLE = {
    "color": "#FF6B6B",
    "weight": 4,
    "fillOpacity": 0.15,
    "fillColor": "#FFE0E0",
    "dashArray": "10,5",
}

HIGHLIGHT_STYLE = {"weight": 4, "color": "#FF6B6B"}

SEOUL_TOTAL_TOOLTIP_STYLE = (
    "background-color: #FF6B6B; color: white; font-family: Arial;"
    " font-size: 14px; padding: 12px; font-weight: bold;"
)

GU_RANKING_TOOLTIP_STYLE = """
    background-color: #F0F8FF;
    border: 2px solid #4A90E2;
    border-radius: 5px;
    box-shadow: 3px;
    font-size: 13px;
"""


def get_gu_ranking_style_function(
    price_quintiles,
    selected_quintile,
    selected_district=None,
    adjacent_districts=None,
    comparison_mode=None,
):
    """자치구 랭킹 지도 스타일 함수를 동적으로 생성하여 반환합니다."""

    # 스타일 함수 생성

    def style_function(feature):
        gu_name = feature["properties"]["SIGUNGU_NM"]
        base_style = {"weight": 2.5, "fillOpacity": 0.3}

        # 선택된 자치구 스타일 (최우선)
        if selected_district and gu_name == selected_district:
            base_style.update(
                {
                    "color": "#FF0000",  # 빨간색
                    "fillColor": "#FF6B6B",
                    "fillOpacity": 0.7,
                    "weight": 4,
                }
            )
        # 비교 자치구 스타일 (두 번째 우선순위) - 비교 모드에 따라 색상 구분
        elif adjacent_districts and gu_name in adjacent_districts:
            if comparison_mode == "similar_price":
                # 유사 매매가: 보라색
                base_style.update(
                    {
                        "color": "#9932CC",  # 보라색
                        "fillColor": "#DDA0DD",
                        "fillOpacity": 0.6,
                        "weight": 3,
                    }
                )
            else:
                # 인접 자치구 (기본): 주황색
                base_style.update(
                    {
                        "color": "#FF8C00",  # 주황색
                        "fillColor": "#FFB347",
                        "fillOpacity": 0.5,
                        "weight": 3,
                    }
                )
        # 기존 구간별 스타일
        elif selected_quintile:
            selected_gus = price_quintiles[selected_quintile]["gus"]
            if gu_name in selected_gus:
                quintile_color = price_quintiles[selected_quintile]["color"]
                base_style.update(
                    {
                        "color": quintile_color,
                        "fillColor": quintile_color,
                        "fillOpacity": 0.6,
                        "weight": 3,
                    }
                )
            else:
                base_style.update(
                    {
                        "color": "#CCCCCC",
                        "fillColor": "#F5F5F5",
                        "fillOpacity": 0.2,
                        "weight": 1,
                    }
                )
        else:
            base_style.update(
                {"color": "#4A90E2", "fillColor": "#E8F4FD", "fillOpacity": 0.1}
            )
        return base_style

    return style_function
