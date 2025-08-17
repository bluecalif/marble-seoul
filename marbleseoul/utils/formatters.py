#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""formatters.py
Marble서울 프로젝트에서 사용하는 포맷팅 유틸리티 함수들을 정의합니다.
"""
from __future__ import annotations
import pandas as pd


def format_price_eok(price_manwon):
    """숫자(만원)를 'X.Y억' 형태의 문자열로 변환."""
    if pd.isna(price_manwon) or price_manwon == 0:
        return "정보 없음"
    eok = price_manwon / 10000
    return f"{eok:.1f}억원"


def format_price_kor(price_manwon):
    """숫자(만원)를 'X억 Y만원' 형태의 문자열로 변환."""
    eok = int(price_manwon // 10000)
    man = int(price_manwon % 10000)
    if eok > 0 and man > 0:
        return f"{eok}억 {man:,}만원"
    if eok > 0:
        return f"{eok}억원"
    return f"{man:,}만원"


def format_gugun_ranking_df(gugun_ranking_df, price_quintiles):
    """자치구 랭킹 데이터프레임을 UI 표시용으로 포맷팅합니다."""
    display_df = gugun_ranking_df.copy()

    # 가격을 억원 형태로 포맷팅
    display_df["price_84m2_manwon"] = display_df["price_84m2_manwon"].apply(
        format_price_eok
    )

    # 표시할 컬럼만 선택
    display_columns = ["gugun", "price_84m2_manwon", "전국기준", "서울기준"]
    display_df = display_df[display_columns]

    # 컬럼명을 한글로 변경
    display_df.rename(
        columns={
            "gugun": "자치구",
            "price_84m2_manwon": "평균 매매가(84m²)",
            "전국기준": "전국 순위",
            "서울기준": "서울 순위",
        },
        inplace=True,
    )

    return display_df
