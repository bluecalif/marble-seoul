# marble/marbleseoul/maps/gu_ranking.py
import folium
import streamlit as st

from ..data import loaders
from ..utils import formatters as fmt
from . import styles


def create_gu_ranking_map(
    gu_ranking_map,
    gugun_ranking_df,
    price_quintiles,
    selected_quintile,
    selected_district=None,
    adjacent_districts=None,
    comparison_mode=None,
):
    """
    자치구별 랭킹 지도를 생성하고 HTML로 반환합니다.

    Args:
        gu_ranking_map (folium.Map): 기본 지도 객체.
        gugun_ranking_df (pd.DataFrame): 자치구별 랭킹 데이터.
        price_quintiles (dict): 가격 5분위 데이터.
        selected_quintile (int | None): 사용자가 선택한 가격 구간.

    Returns:
        str: 지도 HTML 문자열.
    """
    with st.spinner("🔄 자치구별 랭킹 지도 생성 중..."):
        gu_gdf = loaders.load_gu_gdf()

        merged_gdf = gu_gdf.merge(
            gugun_ranking_df, left_on="SIGUNGU_NM", right_on="gugun", how="left"
        )
        merged_gdf["price_84m2_manwon"] = merged_gdf["price_84m2_manwon"].fillna(0)
        merged_gdf["price_eok_str"] = merged_gdf["price_84m2_manwon"].apply(
            fmt.format_price_eok
        )

        style_function = styles.get_gu_ranking_style_function(
            price_quintiles,
            selected_quintile,
            selected_district,
            adjacent_districts,
            comparison_mode,
        )

        # 간단한 팝업으로 롤백 (JavaScript 제거)
        def create_district_popup(district_name, price_str):
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 200px; text-align: center;">
                <h4 style="margin: 5px 0; color: #333;">{district_name}</h4>
                <p style="margin: 5px 0; color: #666;">평균 매매가(84m²): {price_str}</p>
                <p style="margin: 10px 0; color: #999; font-size: 11px;">
                    ⚠️ 지도 클릭 기능은 현재 개발 중입니다.<br>
                    우측 풀다운 메뉴를 사용해주세요.
                </p>
            </div>
            """
            return folium.Popup(popup_html, max_width=250)

        # 각 자치구별로 개별 GeoJSON 레이어 생성 (tooltip + popup 포함)
        for idx, row in merged_gdf.iterrows():
            if row["SIGUNGU_NM"] and row["price_eok_str"]:
                # 클릭 가능한 popup 생성
                popup = create_district_popup(row["SIGUNGU_NM"], row["price_eok_str"])

                # 개별 자치구 데이터 구성 (tooltip을 위해)
                district_data = {
                    "type": "Feature",
                    "properties": {
                        "SIGUNGU_NM": row["SIGUNGU_NM"],
                        "price_eok_str": row["price_eok_str"],
                    },
                    "geometry": row["geometry"].__geo_interface__,
                }

                # 개별 자치구 GeoJSON 생성
                district_geojson = folium.GeoJson(
                    district_data,
                    popup=popup,
                    style_function=lambda x, district=row["SIGUNGU_NM"]: (
                        style_function({"properties": {"SIGUNGU_NM": district}})
                    ),
                    highlight_function=lambda x: styles.HIGHLIGHT_STYLE,
                    tooltip=folium.GeoJsonTooltip(
                        fields=["SIGUNGU_NM", "price_eok_str"],
                        aliases=["자치구:", "평균 매매가(84m²):"],
                        localize=True,
                        sticky=False,
                        labels=True,
                        style=styles.GU_RANKING_TOOLTIP_STYLE,
                    ),
                )

                district_geojson.add_to(gu_ranking_map)
        return gu_ranking_map._repr_html_()


def create_district_zoom_map(
    district_map,
    gugun_ranking_df,
    selected_district,
    adjacent_districts=None,
    comparison_mode=None,
):
    """
    선택된 자치구를 중심으로 줌인된 지도를 생성하고 HTML로 반환합니다.

    Args:
        district_map (folium.Map): 기본 지도 객체 (자치구 중심으로 줌인됨).
        gugun_ranking_df (pd.DataFrame): 자치구별 랭킹 데이터.
        selected_district (str): 선택된 자치구명.

    Returns:
        str: 지도 HTML 문자열.
    """
    with st.spinner(f"🎯 {selected_district} 상세 지도 생성 중..."):
        gu_gdf = loaders.load_gu_gdf()

        # 자치구별 랭킹 데이터와 지리 데이터 병합
        merged_gdf = gu_gdf.merge(
            gugun_ranking_df, left_on="SIGUNGU_NM", right_on="gugun", how="left"
        )
        merged_gdf["price_84m2_manwon"] = merged_gdf["price_84m2_manwon"].fillna(0)
        merged_gdf["price_eok_str"] = merged_gdf["price_84m2_manwon"].apply(
            fmt.format_price_eok
        )

        # 선택된 자치구, 인접 자치구, 다른 자치구들을 구분하여 스타일 적용
        def get_district_zoom_style(feature):
            district_name = feature["properties"]["SIGUNGU_NM"]
            if district_name == selected_district:
                # 선택된 자치구: 강조 표시
                return {
                    "fillColor": "#e31a1c",  # 빨간색
                    "color": "#e31a1c",
                    "weight": 4,
                    "fillOpacity": 0.7,
                    "opacity": 1.0,
                }
            elif adjacent_districts and district_name in adjacent_districts:
                # 비교 자치구: 비교 모드에 따라 색상 구분
                if comparison_mode == "similar_price":
                    # 유사 매매가: 보라색
                    return {
                        "fillColor": "#9932CC",  # 보라색
                        "color": "#9932CC",
                        "weight": 3,
                        "fillOpacity": 0.6,
                        "opacity": 0.8,
                    }
                else:
                    # 인접 자치구 (기본): 주황색
                    return {
                        "fillColor": "#FF8C00",  # 주황색
                        "color": "#FF8C00",
                        "weight": 3,
                        "fillOpacity": 0.5,
                        "opacity": 0.8,
                    }
            else:
                # 다른 자치구: 흐리게 표시
                return {
                    "fillColor": "#d9d9d9",  # 회색
                    "color": "#969696",
                    "weight": 1,
                    "fillOpacity": 0.3,
                    "opacity": 0.5,
                }

        # 지도에 자치구 경계 추가
        gu_layer = folium.GeoJson(
            merged_gdf,
            name="자치구별 경계",
            style_function=get_district_zoom_style,
            highlight_function=lambda x: styles.HIGHLIGHT_STYLE,
        )

        # 선택된 자치구에만 tooltip 추가
        selected_district_data = merged_gdf[
            merged_gdf["SIGUNGU_NM"] == selected_district
        ]
        if not selected_district_data.empty:
            tooltip_fields = ["SIGUNGU_NM", "price_eok_str"]
            tooltip_aliases = ["자치구:", "평균 매매가(84m²):"]

            folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True,
                sticky=False,
                labels=True,
                style=styles.GU_RANKING_TOOLTIP_STYLE,
            ).add_to(gu_layer)

        gu_layer.add_to(district_map)
        return district_map._repr_html_()
