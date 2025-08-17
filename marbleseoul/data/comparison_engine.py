#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""comparison_engine.py
자치구 매매가격 비교 분석 엔진 - 유사 가격대 자치구 탐색
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import streamlit as st


@st.cache_data(show_spinner=False)
def find_similar_price_districts(
    target_district: str, 
    ranking_df: pd.DataFrame, 
    apt_price_df: pd.DataFrame,
    tolerance_pct: float = 15.0,
    max_results: int = 6
) -> Dict:
    """
    선택된 자치구와 유사한 매매가격대의 자치구들을 찾습니다.
    
    Args:
        target_district (str): 대상 자치구명 (예: "강남구")
        ranking_df (pd.DataFrame): 자치구별 랭킹 데이터
        apt_price_df (pd.DataFrame): 아파트 가격 상세 데이터
        tolerance_pct (float): 허용 오차 비율 (기본값: 15%)
        max_results (int): 최대 결과 개수 (기본값: 6개)
        
    Returns:
        Dict: 유사 가격대 자치구 분석 결과
    """
    try:
        # 대상 자치구의 84m² 매매가격 추출
        target_row = ranking_df[ranking_df["gugun"] == target_district]
        
        if target_row.empty:
            return {
                "target_district": target_district,
                "target_price": None,
                "similar_districts": [],
                "comparison_data": pd.DataFrame(),
                "summary": f"{target_district}의 가격 정보를 찾을 수 없습니다.",
                "error": "대상 자치구 데이터 없음"
            }
        
        target_price = target_row["price_84m2_manwon"].iloc[0]
        
        # ±15% 범위 계산
        price_min = target_price * (1 - tolerance_pct / 100)
        price_max = target_price * (1 + tolerance_pct / 100)
        
        # 유사 가격대 자치구 필터링 (자기 자신 제외)
        similar_mask = (
            (ranking_df["price_84m2_manwon"] >= price_min) &
            (ranking_df["price_84m2_manwon"] <= price_max) &
            (ranking_df["gugun"] != target_district)
        )
        
        similar_districts_df = ranking_df[similar_mask].copy()
        
        if similar_districts_df.empty:
            return {
                "target_district": target_district,
                "target_price": target_price,
                "similar_districts": [],
                "comparison_data": pd.DataFrame(),
                "summary": f"{target_district}(₩{target_price:,.0f}만원)와 유사한 가격대(±{tolerance_pct}%)의 자치구를 찾을 수 없습니다.",
                "price_range": f"{price_min:,.0f}~{price_max:,.0f}만원"
            }
        
        # 가격 차이율 및 유사도 점수 계산
        similar_districts_df["price_diff_pct"] = (
            (similar_districts_df["price_84m2_manwon"] - target_price) / target_price * 100
        )
        similar_districts_df["similarity_score"] = (
            100 - abs(similar_districts_df["price_diff_pct"])
        )
        
        # 유사도 순으로 정렬 (높은 점수 우선)
        similar_districts_df = similar_districts_df.sort_values(
            "similarity_score", ascending=False
        )
        
        # 최대 결과 개수 제한
        if len(similar_districts_df) > max_results:
            similar_districts_df = similar_districts_df.head(max_results)
        
        # 각 자치구별 추가 정보 계산 (연식, 세대수)
        additional_info = []
        all_districts = [target_district] + similar_districts_df["gugun"].tolist()
        
        for district in all_districts:
            district_apt_data = apt_price_df[apt_price_df["gugun"] == district]
            if not district_apt_data.empty:
                avg_build_year = district_apt_data["build_year"].mean()
                # district_analyzer와 동일한 세대수 계산 방식 (중복 제거)
                total_households = district_apt_data.groupby("apt_name")["household_count"].first().sum()
                additional_info.append({
                    "gugun": district,
                    "avg_build_year": avg_build_year,
                    "total_households": total_households,
                })
        
        # 추가 정보를 DataFrame으로 변환
        additional_df = pd.DataFrame(additional_info)
        
        # 대상 자치구 정보 추가
        target_full_row = ranking_df[ranking_df["gugun"] == target_district].copy()
        target_full_row["price_diff_pct"] = 0.0
        target_full_row["similarity_score"] = 100.0
        
        # ranking_df의 인덱스 기반 순위 추가 (1부터 시작)
        target_full_row["rank"] = target_full_row.index + 1
        similar_districts_df = similar_districts_df.copy()
        similar_districts_df["rank"] = similar_districts_df.index + 1
        
        # 비교 데이터 생성 (대상 + 유사 자치구들)
        comparison_data = pd.concat([target_full_row, similar_districts_df], ignore_index=True)
        
        # 추가 정보 병합
        comparison_data = comparison_data.merge(additional_df, on="gugun", how="left")
        
        # 대상 자치구를 첫 번째로 정렬
        comparison_data["is_target"] = comparison_data["gugun"] == target_district
        comparison_data = comparison_data.sort_values(
            ["is_target", "similarity_score"], ascending=[False, False]
        )
        
        # 요약 정보 생성
        target_rank = ranking_df[ranking_df["gugun"] == target_district].index[0] + 1
        similar_count = len(similar_districts_df)
        avg_similarity = similar_districts_df["similarity_score"].mean()
        
        summary = (
            f"💰 **{target_district}** (₩{target_price:,.0f}만원, {target_rank}위)와 "
            f"유사한 가격대의 자치구 **{similar_count}개**를 찾았습니다.\n\n"
            f"**가격 범위**: ₩{price_min:,.0f}~{price_max:,.0f}만원 (±{tolerance_pct}%)\n"
            f"**평균 유사도**: {avg_similarity:.1f}점"
        )
        
        return {
            "target_district": target_district,
            "target_price": target_price,
            "similar_districts": similar_districts_df["gugun"].tolist(),
            "comparison_data": comparison_data,
            "summary": summary,
            "price_range": f"{price_min:,.0f}~{price_max:,.0f}만원",
            "tolerance_pct": tolerance_pct,
            "avg_similarity": avg_similarity
        }
        
    except Exception as e:
        st.error(f"유사 가격대 자치구 분석 중 오류 발생: {e}")
        return {
            "target_district": target_district,
            "target_price": None,
            "similar_districts": [],
            "comparison_data": pd.DataFrame(),
            "summary": f"분석 중 오류가 발생했습니다: {e}",
            "error": str(e)
        }


def calculate_price_similarity_matrix(ranking_df: pd.DataFrame) -> pd.DataFrame:
    """
    모든 자치구 간의 가격 유사도 매트릭스를 계산합니다.
    
    Args:
        ranking_df (pd.DataFrame): 자치구별 랭킹 데이터
        
    Returns:
        pd.DataFrame: 자치구 간 가격 유사도 매트릭스
    """
    districts = ranking_df["gugun"].tolist()
    prices = ranking_df["price_84m2_manwon"].values
    
    # 유사도 매트릭스 초기화
    similarity_matrix = pd.DataFrame(
        index=districts, 
        columns=districts, 
        dtype=float
    )
    
    for i, district1 in enumerate(districts):
        for j, district2 in enumerate(districts):
            if i == j:
                similarity_matrix.loc[district1, district2] = 100.0
            else:
                price_diff_pct = abs(prices[i] - prices[j]) / prices[i] * 100
                similarity_score = max(0, 100 - price_diff_pct)
                similarity_matrix.loc[district1, district2] = similarity_score
    
    return similarity_matrix


def get_price_tier_classification(ranking_df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    자치구들을 가격대별로 분류합니다.
    
    Args:
        ranking_df (pd.DataFrame): 자치구별 랭킹 데이터
        
    Returns:
        Dict[str, List[str]]: 가격대별 자치구 분류
    """
    prices = ranking_df["price_84m2_manwon"]
    
    # 5분위수로 가격대 분류
    q1 = prices.quantile(0.2)
    q2 = prices.quantile(0.4)
    q3 = prices.quantile(0.6)
    q4 = prices.quantile(0.8)
    
    tiers = {
        "최고가": ranking_df[prices > q4]["gugun"].tolist(),
        "고가": ranking_df[(prices > q3) & (prices <= q4)]["gugun"].tolist(),
        "중가": ranking_df[(prices > q2) & (prices <= q3)]["gugun"].tolist(),
        "저가": ranking_df[(prices > q1) & (prices <= q2)]["gugun"].tolist(),
        "최저가": ranking_df[prices <= q1]["gugun"].tolist(),
    }
    
    return tiers
