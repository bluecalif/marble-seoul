#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""spatial_analyzer.py
자치구 공간 분석 모듈 - 인접 자치구 찾기 및 공간 관계 분석
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd
from typing import List, Optional
import streamlit as st

from .loaders import load_gu_gdf


@st.cache_data(show_spinner=False)
def find_adjacent_districts(target_district: str) -> List[str]:
    """
    주어진 자치구와 인접한 자치구들을 찾습니다.

    Args:
        target_district (str): 대상 자치구명 (예: "강남구")

    Returns:
        List[str]: 인접한 자치구 이름들의 리스트 (최대 6개)
    """
    try:
        # 자치구 경계 데이터 로드
        gu_gdf = load_gu_gdf()

        if gu_gdf is None or gu_gdf.empty:
            st.error("자치구 경계 데이터를 로드할 수 없습니다.")
            return []

        # 대상 자치구 찾기
        target_row = gu_gdf[gu_gdf["SIGUNGU_NM"] == target_district]

        if target_row.empty:
            st.warning(f"{target_district}를 찾을 수 없습니다.")
            return []

        target_geometry = target_row.geometry.iloc[0]
        adjacent_districts = []

        # 모든 다른 자치구와 인접 관계 확인
        for idx, row in gu_gdf.iterrows():
            district_name = row["SIGUNGU_NM"]

            # 자기 자신은 제외
            if district_name == target_district:
                continue

            # 경계가 접촉하는지 확인 (touches 또는 intersects)
            if target_geometry.touches(row.geometry) or target_geometry.intersects(
                row.geometry
            ):
                adjacent_districts.append(district_name)

        # 최대 6개까지만 반환 (너무 많으면 시각화가 복잡해짐)
        return adjacent_districts[:6]

    except Exception as e:
        st.error(f"인접 자치구 분석 중 오류 발생: {e}")
        return []


@st.cache_data(show_spinner=False)
def get_district_neighbors_info(
    target_district: str, ranking_df: pd.DataFrame, apt_price_df: pd.DataFrame
) -> dict:
    """
    대상 자치구와 인접 자치구들의 종합 정보를 반환합니다.

    Args:
        target_district (str): 대상 자치구명
        ranking_df (pd.DataFrame): 자치구별 랭킹 데이터
        apt_price_df (pd.DataFrame): 아파트 가격 상세 데이터

    Returns:
        dict: 인접 자치구 분석 결과
    """
    adjacent_districts = find_adjacent_districts(target_district)

    if not adjacent_districts:
        return {
            "target_district": target_district,
            "adjacent_districts": [],
            "comparison_data": pd.DataFrame(),
            "summary": f"{target_district}와 인접한 자치구를 찾을 수 없습니다.",
        }

    # 대상 자치구 + 인접 자치구들의 데이터 추출
    all_districts = [target_district] + adjacent_districts
    comparison_data = ranking_df[ranking_df["gugun"].isin(all_districts)].copy()
    
    # ranking_df의 인덱스 기반 순위 추가 (1부터 시작)
    comparison_data["rank"] = comparison_data.index + 1

    # 각 자치구별 추가 정보 계산 (연식, 세대수)
    additional_info = []
    for district in all_districts:
        district_apt_data = apt_price_df[apt_price_df["gugun"] == district]
        if not district_apt_data.empty:
            avg_build_year = district_apt_data["build_year"].mean()
            # district_analyzer와 동일한 세대수 계산 방식 (중복 제거)
            total_households = district_apt_data.groupby("apt_name")["household_count"].first().sum()
            additional_info.append(
                {
                    "gugun": district,
                    "avg_build_year": avg_build_year,
                    "total_households": total_households,
                }
            )

    # 추가 정보를 DataFrame으로 변환하고 comparison_data와 병합
    additional_df = pd.DataFrame(additional_info)
    comparison_data = comparison_data.merge(additional_df, on="gugun", how="left")

    # 대상 자치구를 첫 번째로 정렬
    comparison_data["is_target"] = comparison_data["gugun"] == target_district
    comparison_data = comparison_data.sort_values(
        ["is_target", "price_84m2_manwon"], ascending=[False, False]
    )

    # 요약 정보 생성
    target_rank = (
        ranking_df[ranking_df["gugun"] == target_district].index[0] + 1
        if not ranking_df[ranking_df["gugun"] == target_district].empty
        else "N/A"
    )

    summary = (
        f"📍 **{target_district}** (순위: {target_rank}위)와 인접한 자치구 **{len(adjacent_districts)}개**를 찾았습니다.\n\n"
        f"**인접 자치구**: {', '.join(adjacent_districts)}"
    )

    return {
        "target_district": target_district,
        "adjacent_districts": adjacent_districts,
        "comparison_data": comparison_data,
        "summary": summary,
    }


def calculate_district_distance(district1: str, district2: str) -> Optional[float]:
    """
    두 자치구 중심점 간의 거리를 계산합니다 (km 단위).

    Args:
        district1 (str): 첫 번째 자치구명
        district2 (str): 두 번째 자치구명

    Returns:
        Optional[float]: 거리(km) 또는 None (오류 시)
    """
    try:
        gu_gdf = load_gu_gdf()

        if gu_gdf is None or gu_gdf.empty:
            return None

        # 각 자치구의 중심점 계산
        dist1_row = gu_gdf[gu_gdf["SIGUNGU_NM"] == district1]
        dist2_row = gu_gdf[gu_gdf["SIGUNGU_NM"] == district2]

        if dist1_row.empty or dist2_row.empty:
            return None

        center1 = dist1_row.geometry.centroid.iloc[0]
        center2 = dist2_row.geometry.centroid.iloc[0]

        # 거리 계산 (투영 좌표계로 변환하여 미터 단위 계산 후 km로 변환)
        gdf_projected = gu_gdf.to_crs("EPSG:5179")  # 한국 중부원점 TM 좌표계

        dist1_proj = gdf_projected[
            gdf_projected["SIGUNGU_NM"] == district1
        ].geometry.centroid.iloc[0]
        dist2_proj = gdf_projected[
            gdf_projected["SIGUNGU_NM"] == district2
        ].geometry.centroid.iloc[0]

        distance_m = dist1_proj.distance(dist2_proj)
        distance_km = distance_m / 1000

        return round(distance_km, 2)

    except Exception as e:
        print(f"거리 계산 오류: {e}")
        return None
