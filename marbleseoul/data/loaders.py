#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""loaders.py
Marble서울 프로젝트에서 사용하는 데이터 로딩 함수들을 정의합니다.
st.cache_data를 사용하여 로딩 속도를 최적화합니다.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union

from marbleseoul.utils import constants as const

# 경로 상수는 constants.py에서 통합 관리


@st.cache_data(show_spinner=False)
def load_gu_gdf():  # noqa: D401
    """자치구 GeoDataFrame 로드, CRS 변환 및 경계 통합."""
    shp_path = const.SHP_FILE_PATH
    seoul_gu_mapping = const.SEOUL_GU_MAPPING

    # 여러 인코딩 방식으로 SHP 파일 로드 시도
    gdf_dong = None
    encodings = ["cp949", "euc-kr", "utf-8"]

    for encoding in encodings:
        try:
            gdf_dong = gpd.read_file(shp_path, encoding=encoding)
            break
        except Exception:
            continue

    # 인코딩 없이 시도
    if gdf_dong is None:
        try:
            gdf_dong = gpd.read_file(shp_path)
        except Exception as e:
            st.error(f"SHP 파일 로드 실패: {e}")
            return None

    # 한글 복원 (코드 기반 매핑)
    gdf_dong_fixed = gdf_dong.copy()
    gdf_dong_fixed["SIGUNGU_NM"] = gdf_dong_fixed["SIGUNGU_CD"].map(seoul_gu_mapping)
    gdf_dong_fixed["SIDO_NM"] = "서울특별시"

    # 자치구(SIGUNGU_NM) 기준으로 경계 통합 (1.0m 버퍼링 기법으로 완전한 외곽 경계 생성)
    print("🔄 자치구별 경계 통합 시작... (1.0m 버퍼링 기법)")

    unified_gdf_list = []
    buffer_size = 1.0

    for sigungu_nm in gdf_dong_fixed["SIGUNGU_NM"].unique():
        gu_data = gdf_dong_fixed[gdf_dong_fixed["SIGUNGU_NM"] == sigungu_nm].copy()
        buffered_geoms = [geom.buffer(buffer_size) for geom in gu_data.geometry]
        unified_buffered = unary_union(buffered_geoms)
        unified_geometry = unified_buffered.buffer(-buffer_size)
        first_row = gu_data.iloc[0].copy()
        first_row["geometry"] = unified_geometry
        unified_gdf_list.append(first_row)
        print(f"✅ {sigungu_nm} 경계 통합 완료 (완전한 외곽경계)")

    gdf_gu = gpd.GeoDataFrame(unified_gdf_list, crs=gdf_dong_fixed.crs)
    print(f"🎯 최종 결과: {len(gdf_gu)}개 자치구, 완전한 외곽 경계 생성 완료")

    if gdf_gu.crs is None:
        gdf_gu.set_crs(epsg=5179, inplace=True)
    return gdf_gu.to_crs("EPSG:4326")


@st.cache_data(show_spinner=False)
def load_apt_price_data():
    """아파트 실거래가 통계 데이터 로드 및 전처리."""
    stats_df = pd.read_csv(const.APT_PRICE_STATS_PATH)
    compact_df = pd.read_csv(const.APT_COMPACT_PATH)

    # 아파트 코드와 이름 매핑 테이블 생성
    apt_name_map = compact_df[["aptcode", "complex_name"]].drop_duplicates()

    # 통계 데이터에 아파트 이름 병합
    stats_df = pd.merge(stats_df, apt_name_map, on="aptcode", how="left")

    # built_date를 datetime으로 변환하고 년도만 추출
    stats_df["built_date"] = pd.to_datetime(
        stats_df["built_date"], errors="coerce"
    ).dt.year

    # 실제 컬럼명과 코드에서 사용하는 컬럼명을 일치시킴
    stats_df.rename(
        columns={
            "price_84m2": "price_84m2_manwon",
            "complex_name": "apt_name",  # complex_name을 아파트 이름으로 사용
            "built_date": "build_year",
            "households": "household_count",
        },
        inplace=True,
    )
    return stats_df


@st.cache_data(show_spinner=False)
def load_percentage_rankings():
    """전국/서울 퍼센트 랭킹 데이터 로드."""
    national_path = const.NATIONAL_RANKING_PATH
    seoul_path = const.SEOUL_RANKING_PATH

    try:
        national_df = pd.read_csv(national_path, encoding="utf-8-sig")
        seoul_df = pd.read_csv(seoul_path, encoding="utf-8-sig")

        national_overall = national_df[national_df["period"] == "전체"].copy()
        seoul_overall = seoul_df[seoul_df["period"] == "전체"].copy()

        return national_overall, seoul_overall

    except Exception as e:
        st.warning(f"퍼센트 랭킹 데이터 로드 실패: {e}")
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_dong_stats_data():
    """행정동별 인구 및 매출 통계 데이터 로드."""
    try:
        df = pd.read_csv(const.DONG_STATS_PATH, encoding="utf-8-sig")

        # 총 인구수 계산 (연령대별 합계)
        age_columns = [
            "0_9",
            "10_19",
            "20_29",
            "30_39",
            "40_49",
            "50_59",
            "60_69",
            "70_plus",
        ]
        df["total_population"] = df[age_columns].sum(axis=1)

        return df

    except Exception as e:
        st.warning(f"행정동 통계 데이터 로드 실패: {e}")
        return pd.DataFrame()
