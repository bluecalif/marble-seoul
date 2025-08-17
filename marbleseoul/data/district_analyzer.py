#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""district_analyzer.py
선택된 자치구의 상세 데이터를 분석하는 모듈
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from marbleseoul.data import loaders


@st.cache_data(show_spinner="아파트 정보 분석 중...")
def get_district_apartment_info(apt_price_df: pd.DataFrame, district_name: str) -> dict:
    """
    선택된 자치구의 아파트 종합 정보를 계산합니다.

    Args:
        apt_price_df (pd.DataFrame): 전체 아파트 가격 데이터프레임.
        district_name (str): 분석할 자치구 이름.

    Returns:
        dict: 자치구 아파트 정보 (요약, 상위 5개 단지 등)
    """
    if district_name is None or district_name not in apt_price_df["gugun"].unique():
        return {}

    # 1. 해당 자치구 데이터 필터링
    district_df = apt_price_df[apt_price_df["gugun"] == district_name].copy()

    if district_df.empty:
        return {}

    # 2. 주요 요약 통계 계산
    summary = {
        "총 단지 수": district_df["apt_name"].nunique(),
        "평균 매매가(84m²)": district_df["price_84m2_manwon"].mean(),
        "최고 매매가(84m²)": district_df["price_84m2_manwon"].max(),
        "최저 매매가(84m²)": district_df["price_84m2_manwon"].min(),
        "평균 건축년도": district_df["build_year"].mean(),
        "총 세대수": district_df.groupby("apt_name")["household_count"].first().sum(),
    }

    # 3. 매매가 기준 상위 5개 아파트 단지 정보
    top_5_apts = (
        district_df.groupby("apt_name")
        .agg(
            avg_price_manwon=("price_84m2_manwon", "mean"),
            build_year=("build_year", "first"),
            household_count=("household_count", "first"),
        )
        .sort_values(by="avg_price_manwon", ascending=False)
        .head(5)
        .reset_index()
    )

    return {"summary": summary, "top_5_apts": top_5_apts}
