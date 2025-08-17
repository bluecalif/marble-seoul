# marble/marbleseoul/maps/seoul_total.py
import folium
import geopandas as gpd
import streamlit as st
from shapely.ops import unary_union

from ..data import loaders
from ..utils import formatters as fmt
from . import styles


def create_seoul_total_map(seoul_total_map, latest_month, latest_avg_price):
    """
    서울 전체 경계 지도를 생성하고 HTML로 반환합니다.

    Args:
        seoul_total_map (folium.Map): 기본 지도 객체.
        latest_month (int): 최신 데이터 월.
        latest_avg_price (float): 최신 서울 평균 가격.

    Returns:
        str: 지도 HTML 문자열.
    """
    gu_gdf = loaders.load_gu_gdf()

    with st.spinner("🔄 서울 전체 경계 생성 중... (1.0m 버퍼링 기법)"):
        gu_gdf_projected = gu_gdf.to_crs("EPSG:5179")
        buffered_geometries = gu_gdf_projected.geometry.buffer(1.0)
        seoul_total_boundary_projected = unary_union(buffered_geometries).buffer(-1.0)
        seoul_total_gdf = gpd.GeoDataFrame(
            [1], geometry=[seoul_total_boundary_projected], crs="EPSG:5179"
        )
        seoul_total_boundary = seoul_total_gdf.to_crs("EPSG:4326").geometry.iloc[0]

    year = latest_month // 100
    month = latest_month % 100
    seoul_total_price_str = fmt.format_price_eok(latest_avg_price)

    seoul_boundary_layer = folium.GeoJson(
        seoul_total_boundary,
        name="서울특별시 전체",
        style_function=lambda x: styles.SEOUL_TOTAL_STYLE,
        highlight_function=lambda x: styles.HIGHLIGHT_STYLE,
    )

    folium.Tooltip(
        text=f"서울특별시 전체<br>{year}년 {month}월 평균: {seoul_total_price_str}",
        style=styles.SEOUL_TOTAL_TOOLTIP_STYLE,
    ).add_to(seoul_boundary_layer)

    seoul_boundary_layer.add_to(seoul_total_map)
    return seoul_total_map._repr_html_()
