#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""data_display.py
분석된 데이터를 Streamlit UI에 표시하는 모듈
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from marbleseoul.utils import formatters as fmt


def display_district_info(district_info: dict):
    """
    자치구 상세 정보를 Expander 내에 테이블로 표시합니다.

    Args:
        district_info (dict): district_analyzer.get_district_apartment_info가 반환한 데이터.
    """
    if not district_info:
        return

    summary = district_info.get("summary", {})
    top_5_apts = district_info.get("top_5_apts")

    with st.expander("📊 아파트 종합 정보", expanded=True):
        if not summary:
            st.warning("요약 정보가 없습니다.")
            return

        # 요약 정보를 2열로 표시
        col1, col2 = st.columns(2)
        col1.metric("총 단지 수", f"{summary.get('총 단지 수', 0):,} 개")
        col1.metric("평균 건축년도", f"{summary.get('평균 건축년도', 0):.0f} 년")
        col2.metric("총 세대수", f"{summary.get('총 세대수', 0):,} 세대")
        col2.metric(
            "평균 매매가(84m²)",
            fmt.format_price_eok(summary.get("평균 매매가(84m²)", 0)),
        )

        st.divider()

        # 상위 5개 아파트 정보 표시
        st.markdown("##### 📈 매매가 Top 5 아파트")
        if top_5_apts is not None and not top_5_apts.empty:
            # 표시용 데이터프레임 생성
            display_df = top_5_apts.copy()
            display_df["avg_price_eok"] = display_df["avg_price_manwon"].apply(
                fmt.format_price_eok
            )
            display_df.rename(
                columns={
                    "apt_name": "아파트명",
                    "build_year": "건축년도",
                    "household_count": "세대수",
                    "avg_price_eok": "평균 매매가(84m²)",
                },
                inplace=True,
            )
            st.dataframe(
                display_df[["아파트명", "평균 매매가(84m²)", "건축년도", "세대수"]],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("해당 자치구의 Top 5 아파트 정보를 불러올 수 없습니다.")


def display_dong_info(dong_info):
    """행정동 아파트 종합 정보를 UI에 표시합니다."""
    st.subheader("📊 행정동 아파트 정보")
    summary = dong_info["summary"]

    # 6개의 컬럼으로 메트릭 표시
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    cols = [col1, col2, col3, col4, col5, col6]
    metrics = list(summary.items())

    for i, col in enumerate(cols):
        if i < len(metrics):
            label, value = metrics[i]
            col.metric(label, value)

    st.markdown("##### 상위 5개 아파트 (평균 가격 기준)")
    st.dataframe(dong_info["top_5"], use_container_width=True, hide_index=True)
