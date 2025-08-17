#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""processors.py
데이터 가공 및 변환 로직
"""
from __future__ import annotations

import pandas as pd


def process_monthly_avg(apt_price_df: pd.DataFrame) -> tuple[pd.Series, int, float]:
    """
    아파트 가격 데이터프레임에서 서울 전체 월별 평균 가격,
    가장 최신 월, 최신 월의 평균 가격을 계산하여 반환합니다.
    """
    seoul_monthly_avg_price = (
        apt_price_df.groupby("deal_ym")["price_84m2_manwon"].mean().sort_index()
    )
    latest_month = seoul_monthly_avg_price.index.max()
    latest_avg_price = seoul_monthly_avg_price.loc[latest_month]
    return seoul_monthly_avg_price, latest_month, latest_avg_price
    