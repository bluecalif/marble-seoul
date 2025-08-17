#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""visualization.py
자치구 비교 데이터 시각화 모듈 - Plotly 기반 인터랙티브 차트
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional


def create_price_comparison_chart(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    자치구별 매매가격 비교 바차트를 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드 ("adjacent" 또는 "similar_price")

    Returns:
        go.Figure: Plotly 차트 객체
    """
    # 데이터 준비
    chart_data = comparison_data.copy()

    # 색상 매핑
    colors = []
    for district in chart_data["gugun"]:
        if district == target_district:
            colors.append("#FF0000")  # 빨간색 (기준 자치구)
        elif comparison_mode == "similar_price":
            colors.append("#9932CC")  # 보라색 (유사 가격)
        else:
            colors.append("#FF8C00")  # 주황색 (인접 자치구)

    # 바차트 생성
    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_data["gugun"],
                y=chart_data["price_84m2_manwon"],
                marker_color=colors,
                text=chart_data["price_84m2_manwon"].apply(lambda x: f"₩{x:,.0f}만원"),
                textposition="auto",
                hovertemplate=(
                    "<b>%{x}</b><br>" "매매가격: ₩%{y:,.0f}만원<br>" "<extra></extra>"
                ),
            )
        ]
    )

    # 레이아웃 설정
    fig.update_layout(
        title={
            "text": f"📊 자치구별 84m² 매매가격 비교 ({target_district} 기준)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        xaxis_title="자치구",
        yaxis_title="매매가격 (만원)",
        showlegend=False,
        height=500,
        margin=dict(t=60, b=60, l=60, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # 축 스타일링
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat=",")

    return fig


def create_build_year_comparison_chart(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    자치구별 평균 건축년도 비교 바차트를 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        go.Figure: Plotly 차트 객체
    """
    # 데이터 준비
    chart_data = comparison_data.copy()

    # NaN 값 처리
    chart_data = chart_data.dropna(subset=["avg_build_year"])

    if chart_data.empty:
        # 데이터가 없는 경우 빈 차트 반환
        fig = go.Figure()
        fig.add_annotation(
            text="건축년도 데이터가 없습니다.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor="center",
            yanchor="middle",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # 색상 매핑
    colors = []
    for district in chart_data["gugun"]:
        if district == target_district:
            colors.append("#FF0000")  # 빨간색
        elif comparison_mode == "similar_price":
            colors.append("#9932CC")  # 보라색
        else:
            colors.append("#FF8C00")  # 주황색

    # 바차트 생성
    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_data["gugun"],
                y=chart_data["avg_build_year"],
                marker_color=colors,
                text=chart_data["avg_build_year"].apply(lambda x: f"{x:.0f}년"),
                textposition="auto",
                hovertemplate=(
                    "<b>%{x}</b><br>" "평균 건축년도: %{y:.0f}년<br>" "<extra></extra>"
                ),
            )
        ]
    )

    # 레이아웃 설정
    fig.update_layout(
        title={
            "text": f"🏗️ 자치구별 평균 건축년도 비교 ({target_district} 기준)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        xaxis_title="자치구",
        yaxis_title="평균 건축년도 (년)",
        showlegend=False,
        height=500,
        margin=dict(t=60, b=60, l=60, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # 축 스타일링
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat=".0f")

    return fig


def create_dual_axis_comparison_chart(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    매매가격과 건축년도를 이중축으로 비교하는 차트를 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        go.Figure: Plotly 차트 객체
    """
    # 데이터 준비
    chart_data = comparison_data.dropna(subset=["avg_build_year"]).copy()

    if chart_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="비교 데이터가 충분하지 않습니다.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor="center",
            yanchor="middle",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # 서브플롯 생성 (이중축)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 색상 설정
    price_colors = []
    year_colors = []

    for district in chart_data["gugun"]:
        if district == target_district:
            price_colors.append("#FF0000")  # 빨간색
            year_colors.append("#FF6B6B")  # 연한 빨간색
        elif comparison_mode == "similar_price":
            price_colors.append("#9932CC")  # 보라색
            year_colors.append("#DDA0DD")  # 연한 보라색
        else:
            price_colors.append("#FF8C00")  # 주황색
            year_colors.append("#FFB347")  # 연한 주황색

    # 매매가격 바차트 (Primary Y축)
    fig.add_trace(
        go.Bar(
            x=chart_data["gugun"],
            y=chart_data["price_84m2_manwon"],
            name="매매가격",
            marker_color=price_colors,
            opacity=0.8,
            hovertemplate="<b>%{x}</b><br>매매가격: ₩%{y:,.0f}만원<extra></extra>",
        ),
        secondary_y=False,
    )

    # 건축년도 라인차트 (Secondary Y축)
    fig.add_trace(
        go.Scatter(
            x=chart_data["gugun"],
            y=chart_data["avg_build_year"],
            mode="lines+markers",
            name="평균 건축년도",
            line=dict(color="#2E8B57", width=3),
            marker=dict(color="#2E8B57", size=8),
            hovertemplate="<b>%{x}</b><br>평균 건축년도: %{y:.0f}년<extra></extra>",
        ),
        secondary_y=True,
    )

    # 축 제목 설정
    fig.update_xaxes(title_text="자치구", tickangle=45)
    fig.update_yaxes(title_text="매매가격 (만원)", secondary_y=False, tickformat=",")
    fig.update_yaxes(
        title_text="평균 건축년도 (년)", secondary_y=True, tickformat=".0f"
    )

    # 레이아웃 설정
    fig.update_layout(
        title={
            "text": f"📈 매매가격 vs 건축년도 비교 ({target_district} 기준)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        height=600,
        margin=dict(t=60, b=60, l=60, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_household_comparison_chart(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    자치구별 총 세대수 비교 바차트를 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        go.Figure: Plotly 차트 객체
    """
    # 데이터 준비
    chart_data = comparison_data.dropna(subset=["total_households"]).copy()

    if chart_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="세대수 데이터가 없습니다.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor="center",
            yanchor="middle",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # 색상 매핑
    colors = []
    for district in chart_data["gugun"]:
        if district == target_district:
            colors.append("#FF0000")  # 빨간색
        elif comparison_mode == "similar_price":
            colors.append("#9932CC")  # 보라색
        else:
            colors.append("#FF8C00")  # 주황색

    # 바차트 생성
    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_data["gugun"],
                y=chart_data["total_households"],
                marker_color=colors,
                text=chart_data["total_households"].apply(lambda x: f"{x:,.0f}세대"),
                textposition="auto",
                hovertemplate=(
                    "<b>%{x}</b><br>" "총 세대수: %{y:,.0f}세대<br>" "<extra></extra>"
                ),
            )
        ]
    )

    # 레이아웃 설정
    fig.update_layout(
        title={
            "text": f"🏠 자치구별 총 세대수 비교 ({target_district} 기준)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        xaxis_title="자치구",
        yaxis_title="총 세대수 (세대)",
        showlegend=False,
        height=500,
        margin=dict(t=60, b=60, l=60, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # 축 스타일링
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat=",")

    return fig


@st.cache_data(show_spinner=False)
def generate_all_comparison_charts(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> Dict[str, go.Figure]:
    """
    모든 비교 차트를 한 번에 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        Dict[str, go.Figure]: 차트 이름별 Plotly 객체 딕셔너리
    """
    try:
        charts = {}

        # 1. 매매가격 비교 차트
        charts["price"] = create_price_comparison_chart(
            comparison_data, target_district, comparison_mode
        )

        # 2. 건축년도 비교 차트
        charts["build_year"] = create_build_year_comparison_chart(
            comparison_data, target_district, comparison_mode
        )

        # 3. 이중축 비교 차트
        charts["dual_axis"] = create_dual_axis_comparison_chart(
            comparison_data, target_district, comparison_mode
        )

        # 4. 세대수 비교 차트
        charts["households"] = create_household_comparison_chart(
            comparison_data, target_district, comparison_mode
        )

        return charts

    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {e}")
        return {}


def create_population_sales_dual_axis_chart(
    comparison_data: pd.DataFrame,
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    자치구별 인구수(막대) vs 매출액(선) 이중축 차트를 생성합니다.

    Args:
        comparison_data (pd.DataFrame): 비교 데이터 (인구/매출 포함)
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        go.Figure: Plotly 이중축 차트 객체
    """
    # 데이터 준비
    chart_data = comparison_data.dropna(
        subset=["total_population", "total_sales_billion"]
    ).copy()

    if chart_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="인구/매출 데이터가 없습니다.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor="center",
            yanchor="middle",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # 색상 매핑
    colors = []
    for district in chart_data["gugun"]:
        if district == target_district:
            colors.append("#FF0000")  # 빨간색
        elif comparison_mode == "similar_price":
            colors.append("#9932CC")  # 보라색
        else:
            colors.append("#FF8C00")  # 주황색

    # 이중축 차트 생성
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=[f"📊 {target_district} 및 비교 자치구 인구수 vs 매출액 비교"],
    )

    # 1차 Y축: 인구수 (막대그래프)
    fig.add_trace(
        go.Bar(
            x=chart_data["gugun"],
            y=chart_data["total_population"],
            name="총 인구수",
            marker_color=colors,
            text=chart_data["total_population"].apply(lambda x: f"{x:,.0f}명"),
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>" "총 인구수: %{y:,.0f}명<br>" "<extra></extra>"
            ),
            opacity=0.7,
        ),
        secondary_y=False,
    )

    # 2차 Y축: 매출액 (선그래프)
    fig.add_trace(
        go.Scatter(
            x=chart_data["gugun"],
            y=chart_data["total_sales_billion"],
            mode="lines+markers",
            name="총 매출액",
            line=dict(color="#2E86C1", width=3),
            marker=dict(size=10, color="#2E86C1", line=dict(width=2, color="white")),
            text=chart_data["total_sales_billion"].apply(lambda x: f"{x:,.1f}억원"),
            textposition="top center",
            hovertemplate=(
                "<b>%{x}</b><br>" "총 매출액: %{y:,.1f}억원<br>" "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    # Y축 설정
    fig.update_yaxes(
        title_text="총 인구수 (명)",
        secondary_y=False,
        showgrid=True,
        gridcolor="lightgray",
    )
    fig.update_yaxes(title_text="총 매출액 (억원)", secondary_y=True, showgrid=False)

    # 레이아웃 설정
    fig.update_layout(
        title={
            "text": f"📈 인구수 vs 매출액 이중축 비교",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        xaxis_title="자치구",
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80, b=50, l=50, r=50),
    )

    return fig


def generate_population_sales_chart(
    comparison_districts: List[str],
    target_district: str,
    comparison_mode: str = "adjacent",
) -> go.Figure:
    """
    인구/매출 이중축 차트를 생성합니다.

    Args:
        comparison_districts (List[str]): 비교할 자치구 리스트
        target_district (str): 기준 자치구
        comparison_mode (str): 비교 모드

    Returns:
        go.Figure: Plotly 차트 객체
    """
    from .population_analyzer import get_comparison_population_sales_data

    # 대상 자치구도 포함하여 전체 자치구 리스트 생성
    all_districts = [target_district] + comparison_districts

    # 인구/매출 데이터 로드
    pop_sales_data = get_comparison_population_sales_data(all_districts)

    if pop_sales_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="인구/매출 데이터를 로드할 수 없습니다.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor="center",
            yanchor="middle",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    return create_population_sales_dual_axis_chart(
        pop_sales_data, target_district, comparison_mode
    )
