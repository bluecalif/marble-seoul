#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rankings.py
랭킹 계산 관련 로직
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from marbleseoul.data import loaders
from marbleseoul.utils import constants as const
from marbleseoul.utils import formatters as fmt


def find_percentile_rank(price_manwon, ranking_df):
    """특정 가격에 대한 퍼센트 랭킹 찾기."""
    if len(ranking_df) == 0:
        return None

    # 해당 가격보다 낮은 기준값을 가진 가장 높은 퍼센트 찾기
    matching_rows = ranking_df[ranking_df["threshold_price_manwon"] <= price_manwon]

    if len(matching_rows) == 0:
        return 100  # 가장 낮은 구간

    # 가장 낮은 퍼센트 (즉, 가장 높은 순위) 반환
    return matching_rows["percentile"].min()


def calculate_gugun_ranking(df, deal_month):
    """특정 월의 자치구별 국평 매매가 랭킹 계산 (퍼센트 랭킹 포함)."""
    monthly_data = df[df["deal_ym"] == deal_month]
    ranking = (
        monthly_data.groupby("gugun")["price_84m2_manwon"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    ranking.index = ranking.index + 1  # 1부터 시작하는 순위

    # 퍼센트 랭킹 데이터 로드
    national_ranking, seoul_ranking = loaders.load_percentage_rankings()

    # 각 자치구에 대해 전국/서울 퍼센트 랭킹 계산
    if len(national_ranking) > 0 and len(seoul_ranking) > 0:
        ranking["전국상위퍼센트"] = ranking["price_84m2_manwon"].apply(
            lambda price: find_percentile_rank(price, national_ranking)
        )
        ranking["서울내상위퍼센트"] = ranking["price_84m2_manwon"].apply(
            lambda price: find_percentile_rank(price, seoul_ranking)
        )

        # 퍼센트 표시 문자열 생성
        ranking["전국기준"] = ranking["전국상위퍼센트"].apply(
            lambda pct: f"상위 {pct}%" if pct is not None else "N/A"
        )
        ranking["서울기준"] = ranking["서울내상위퍼센트"].apply(
            lambda pct: f"상위 {pct}%" if pct is not None else "N/A"
        )
    else:
        # 퍼센트 랭킹 데이터가 없는 경우 기본값
        ranking["전국상위퍼센트"] = None
        ranking["서울내상위퍼센트"] = None
        ranking["전국기준"] = "N/A"
        ranking["서울기준"] = "N/A"

    return ranking.head(25)


@st.cache_data(show_spinner=False)
def calculate_price_quintiles(ranking_df):
    """자치구 랭킹 데이터를 5구간으로 분류."""
    price_series = ranking_df.set_index("gugun")["price_84m2_manwon"]
    quintiles = {}

    # 5분위로 나누기 (상위 20%씩)
    for i in range(5):
        start_idx = i * 5
        end_idx = start_idx + 5
        quintile_gus = price_series.iloc[start_idx:end_idx].index.tolist()
        quintile_prices = price_series.iloc[start_idx:end_idx].values

        quintiles[i + 1] = {
            "gus": quintile_gus,
            "label": f"{i+1}구간",
            "description": f"상위 {20*(i+1)}%",
            "color": const.QUINTILE_COLORS[i],  # 색상 코드를 상수에서 가져옴
            "count": len(quintile_gus),
            "price_range": f"{fmt.format_price_eok(quintile_prices.min())} ~ {fmt.format_price_eok(quintile_prices.max())}",
            "price_min": quintile_prices.min(),
            "price_max": quintile_prices.max(),
        }

    return quintiles