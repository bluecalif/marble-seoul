#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mode_renderer.py
모드별 UI 렌더링 함수 모듈 (단계 7-1-2)
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from marbleseoul.core import cache_manager
from marbleseoul.data import (
    district_analyzer,
    spatial_analyzer,
    comparison_engine,
)
from marbleseoul.ui import map_controls, chat_interface, data_display
from marbleseoul.utils import formatters as fmt


def render_overview_mode(
    st_session_state, latest_month, latest_avg_price, gugun_ranking_df
) -> tuple:
    """서울 전체 현황 모드 렌더링"""

    # === 서울 전체 현황 대시보드 ===
    st.markdown("### 🏢 서울시 아파트 매매가 현황")

    # 핵심 지표 요약
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="📅 기준월", value=f"{latest_month}", help="최신 데이터 기준월")

    with col2:
        avg_price_eok = fmt.format_price_eok(latest_avg_price)
        st.metric(
            label="🏠 서울시 평균 매매가",
            value=f"{avg_price_eok}",
            help="국평(84m²) 기준 평균 매매가",
        )

    with col3:
        total_districts = len(gugun_ranking_df)
        st.metric(
            label="🗺️ 자치구 수",
            value=f"{total_districts}개",
            help="데이터 포함 자치구 개수",
        )

    # 최고가/최저가 자치구 하이라이트
    st.markdown("#### 🎯 가격 순위 하이라이트")

    col_high, col_low = st.columns(2)

    with col_high:
        highest = gugun_ranking_df.iloc[0]  # 1위 (가장 높은 가격)
        highest_price = fmt.format_price_eok(highest["price_84m2_manwon"])
        st.success(
            f"""
        **🥇 최고가 자치구**  
        **{highest['gugun']}**  
        {highest_price}
        """
        )

    with col_low:
        lowest = gugun_ranking_df.iloc[-1]  # 마지막 (가장 낮은 가격)
        lowest_price = fmt.format_price_eok(lowest["price_84m2_manwon"])
        st.info(
            f"""
        **🏷️ 최저가 자치구**  
        **{lowest['gugun']}**  
        {lowest_price}
        """
        )

    # 상위 5개 자치구 미리보기
    st.markdown("#### 📊 매매가 상위 5개 자치구")

    top5_df = gugun_ranking_df.head(5)[["gugun", "price_84m2_manwon"]].copy()
    # 순위는 인덱스 기반으로 계산 (1부터 시작)
    top5_df["순위"] = range(1, len(top5_df) + 1)
    top5_df["price_84m2_manwon"] = top5_df["price_84m2_manwon"].apply(
        lambda x: fmt.format_price_eok(x)
    )
    top5_df.columns = ["자치구", "국평(84m²) 매매가", "순위"]

    st.dataframe(
        top5_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "순위": st.column_config.NumberColumn(
                "순위", help="25개 자치구 중 순위", format="%d위"
            )
        },
    )

    # 안내 메시지
    st.info(
        "💡 **다른 모드로 전환**하거나 **챗봇에 질문**하여 더 자세한 정보를 확인하세요!"
    )

    # 챗봇 영역
    chat_action = chat_interface.render_chat_interface(
        st_session_state, latest_month, latest_avg_price, gugun_ranking_df
    )

    # 모드별 컨텍스트 생성
    highest = gugun_ranking_df.iloc[0]
    lowest = gugun_ranking_df.iloc[-1]
    top5_districts = gugun_ranking_df.head(5)["gugun"].tolist()

    context_data = {
        "mode": "overview",
        "seoul_avg_price": latest_avg_price,
        "total_districts": len(gugun_ranking_df),
        "highest_district": {
            "name": highest["gugun"],
            "price": highest["price_84m2_manwon"],
        },
        "lowest_district": {
            "name": lowest["gugun"],
            "price": lowest["price_84m2_manwon"],
        },
        "top5_districts": top5_districts,
    }

    return context_data, chat_action


def render_ranking_mode(
    st_session_state, latest_month, latest_avg_price, gugun_ranking_df, price_quintiles
) -> tuple:
    """가격 5분위 랭킹 모드 렌더링"""

    # === 가격 5분위 대시보드 ===
    st.markdown("### 📊 서울시 자치구 가격 5분위 분석")

    # 전체 개요
    st.info(
        f"**{latest_month}** 기준 서울시 25개 자치구를 **가격 5분위**로 분류하여 분석합니다."
    )

    # 5분위별 요약 카드
    cols = st.columns(5)

    for i, col in enumerate(cols, 1):
        quintile_data = price_quintiles[i]
        with col:
            st.markdown(
                f"""
            <div style="padding: 10px; border-left: 4px solid {quintile_data['color']}; background-color: rgba(128,128,128,0.1); border-radius: 5px;">
                <h4 style="margin: 0; color: {quintile_data['color']};">{quintile_data['label']}</h4>
                <p style="margin: 5px 0; font-size: 12px;">{quintile_data['description']}</p>
                <p style="margin: 5px 0; font-weight: bold;">{quintile_data['price_range']}</p>
                <p style="margin: 0; font-size: 11px; color: #666;">{quintile_data['count']}개 자치구</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # 분위별 상세 정보
    st.markdown("#### 🎯 분위별 자치구 현황")

    # 탭으로 분위별 정보 표시
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            f"1구간 (상위 20%)",
            f"2구간 (상위 40%)",
            f"3구간 (상위 60%)",
            f"4구간 (상위 80%)",
            f"5구간 (상위 100%)",
        ]
    )

    tabs = [tab1, tab2, tab3, tab4, tab5]

    for i, tab in enumerate(tabs, 1):
        with tab:
            quintile_data = price_quintiles[i]

            # 해당 분위 자치구들의 상세 데이터
            quintile_districts = gugun_ranking_df[
                gugun_ranking_df["gugun"].isin(quintile_data["gus"])
            ].copy()

            # 순위 추가 (인덱스 기반)
            quintile_districts["순위"] = range(
                (i - 1) * 5 + 1, (i - 1) * 5 + len(quintile_districts) + 1
            )

            # 분위 특성 요약
            col_summary, col_table = st.columns([1, 2])

            with col_summary:
                avg_price = quintile_districts["price_84m2_manwon"].mean()
                st.metric(
                    label="🏠 평균 매매가",
                    value=fmt.format_price_eok(avg_price),
                    help=f"{quintile_data['label']} 평균값",
                )

                if len(quintile_districts) > 0:
                    highest_gu = quintile_districts.iloc[0]["gugun"]
                    lowest_gu = quintile_districts.iloc[-1]["gugun"]
                    st.write(f"**🥇 최고**: {highest_gu}")
                    st.write(f"**🥉 최저**: {lowest_gu}")

            with col_table:
                # 자치구 목록 테이블
                display_df = quintile_districts[
                    ["순위", "gugun", "price_84m2_manwon"]
                ].copy()
                display_df["price_84m2_manwon"] = display_df["price_84m2_manwon"].apply(
                    lambda x: fmt.format_price_eok(x)
                )
                display_df.columns = ["순위", "자치구", "국평(84m²) 매매가"]

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "순위": st.column_config.NumberColumn(
                            "순위", help="전체 25개 자치구 중 순위", format="%d위"
                        )
                    },
                )

    # 분위 간 비교 차트
    st.markdown("#### 📈 분위별 가격 분포")

    # 간단한 분위별 평균가격 비교
    quintile_summary = []
    for i in range(1, 6):
        q_data = price_quintiles[i]
        avg_price = (q_data["price_min"] + q_data["price_max"]) / 2
        quintile_summary.append(
            {"분위": f"{i}구간", "평균가격": avg_price, "색상": q_data["color"]}
        )

    # Streamlit의 간단한 차트 표시
    import pandas as pd

    chart_df = pd.DataFrame(quintile_summary)
    st.bar_chart(chart_df.set_index("분위")["평균가격"], use_container_width=True)

    # 안내 메시지
    st.success(
        "💡 **지도에서 구간별 색상**으로 자치구를 확인하거나, **챗봇에 구간별 질문**을 해보세요!"
    )

    # 챗봇 영역
    chat_action = chat_interface.render_chat_interface(
        st_session_state, latest_month, latest_avg_price, gugun_ranking_df
    )

    # 모드별 컨텍스트 생성
    current_quintile = st_session_state.get("selected_quintile", None)
    quintile_info = {}

    if current_quintile and current_quintile in price_quintiles:
        quintile_data = price_quintiles[current_quintile]
        quintile_info = {
            "quintile": current_quintile,
            "label": quintile_data["label"],
            "price_range": quintile_data["price_range"],
            "districts": quintile_data["gus"],
            "count": len(quintile_data["gus"]),
        }

    context_data = {
        "mode": "ranking",
        "total_quintiles": 5,
        "selected_quintile": quintile_info,
        "all_quintiles": {
            i: {
                "label": price_quintiles[i]["label"],
                "price_range": price_quintiles[i]["price_range"],
                "count": len(price_quintiles[i]["gus"]),
            }
            for i in range(1, 6)
        },
    }

    return context_data, chat_action


def render_district_mode(
    st_session_state, latest_month, latest_avg_price, gugun_ranking_df, apt_price_df
) -> tuple:
    """자치구 선택 모드 렌더링"""
    # 자치구 선택 풀다운
    all_districts = ["자치구를 선택하세요"] + sorted(gugun_ranking_df["gugun"].tolist())

    if st_session_state.selected_district:
        st.markdown("#### 🎯 선택된 자치구")
        try:
            current_index = all_districts.index(st_session_state.selected_district)
        except ValueError:
            current_index = 0
        label_text = "다른 자치구로 변경하시겠습니까?"
    else:
        st.markdown("#### 🏗️ 자치구 선택")
        current_index = 0
        label_text = "분석하고 싶은 자치구를 선택해주세요."

    selected_district_new = st.selectbox(
        label_text,
        all_districts,
        index=current_index,
        key="district_select_main",
        help="자치구를 선택하면 해당 자치구의 상세 분석이 시작됩니다.",
    )

    # 자치구가 선택/변경된 경우 처리
    if (
        selected_district_new != "자치구를 선택하세요"
        and selected_district_new != st_session_state.selected_district
    ):
        cache_manager.select_district(selected_district_new)

        district_info_new = gugun_ranking_df[
            gugun_ranking_df["gugun"] == selected_district_new
        ]
        if not district_info_new.empty:
            rank = district_info_new.index[0] + 1
            price = district_info_new["price_84m2_manwon"].iloc[0]
            price_str = fmt.format_price_eok(price)

            change_msg = (
                f"🔄 **{selected_district_new}**로 변경되었습니다!\n\n"
                f"- **서울시 매매가 순위**: **{rank}위**\n"
                f"- **국평(84m²) 평균 매매가**: **{price_str}**"
            )
            cache_manager.add_message("assistant", change_msg)
        st.rerun()

    # 자치구가 선택되었을 때 자치구 정보 표시
    if st_session_state.selected_district:
        district_info = district_analyzer.get_district_apartment_info(
            apt_price_df, st_session_state.selected_district
        )
        data_display.display_district_info(district_info)

        # 행정동 드롭다운 추가 (비교 모드가 아닐 때만 표시)
        if not getattr(st_session_state, "comparison_mode", None):
            st.markdown("---")
            st.markdown("##### 🏠 행정동별 상세 분석")

            # 선택된 자치구의 행정동 목록 추출
            district_data = apt_price_df[
                apt_price_df["gugun"] == st_session_state.selected_district
            ]
            if not district_data.empty:
                dong_list = ["행정동을 선택하세요"] + sorted(
                    district_data["dong"].unique().tolist()
                )
                selected_dong = st.selectbox(
                    f"{st_session_state.selected_district}의 행정동을 선택해주세요:",
                    dong_list,
                    key="dong_selector",
                )

                # 행정동이 선택되었을 때 상세 정보 표시
                if selected_dong != "행정동을 선택하세요":
                    from marbleseoul.data import dong_analyzer

                    dong_info = dong_analyzer.get_dong_apartment_info(
                        apt_price_df, st_session_state.selected_district, selected_dong
                    )
                    if dong_info:
                        data_display.display_dong_info(dong_info)
                    else:
                        st.warning(f"{selected_dong}에 대한 아파트 데이터가 없습니다.")
            else:
                st.warning(
                    f"{st_session_state.selected_district}에 대한 데이터를 찾을 수 없습니다."
                )

    # 챗봇 영역 (맨 아래 배치)
    st.markdown("---")
    chat_action = chat_interface.render_chat_interface(
        st_session_state, latest_month, latest_avg_price, gugun_ranking_df
    )

    # 모드별 컨텍스트 생성
    context_data = {"mode": "district"}

    if st_session_state.selected_district:
        # 선택된 자치구 정보
        district_info = gugun_ranking_df[
            gugun_ranking_df["gugun"] == st_session_state.selected_district
        ]

        if not district_info.empty:
            rank = district_info.index[0] + 1
            price = district_info["price_84m2_manwon"].iloc[0]

            # 자치구 상세 정보 (선택적)
            apt_info = None
            try:
                apt_info = district_analyzer.get_district_apartment_info(
                    apt_price_df, st_session_state.selected_district
                )
            except Exception:
                pass

            context_data.update(
                {
                    "selected_district": st_session_state.selected_district,
                    "rank": rank,
                    "price": price,
                    "apt_info": (
                        {
                            "total_complexes": (
                                apt_info.get("summary", {}).get("총 단지 수")
                                if apt_info
                                else None
                            ),
                            "total_households": (
                                apt_info.get("summary", {}).get("총 세대수")
                                if apt_info
                                else None
                            ),
                            "avg_build_year": (
                                apt_info.get("summary", {}).get("평균 건축년도")
                                if apt_info
                                else None
                            ),
                            "min_price": (
                                apt_info.get("summary", {}).get("최저 매매가(84m²)")
                                if apt_info
                                else None
                            ),
                            "max_price": (
                                apt_info.get("summary", {}).get("최고 매매가(84m²)")
                                if apt_info
                                else None
                            ),
                        }
                        if apt_info
                        else None
                    ),
                }
            )

    return context_data, chat_action


def render_comparison_mode(
    st_session_state, latest_month, latest_avg_price, gugun_ranking_df, apt_price_df
) -> tuple:
    """자치구 비교 모드 렌더링"""
    # 자치구 선택 풀다운
    all_districts = ["자치구를 선택하세요"] + sorted(gugun_ranking_df["gugun"].tolist())

    if st_session_state.selected_district:
        current_index = all_districts.index(st_session_state.selected_district)
    else:
        current_index = 0

    selected_district_new = st.selectbox(
        "비교할 기준 자치구를 선택하세요",
        all_districts,
        index=current_index,
        key="district_select_comparison",
        help="선택한 자치구를 기준으로 다른 자치구와 비교합니다.",
    )

    # 자치구가 선택/변경된 경우 처리
    if (
        selected_district_new != "자치구를 선택하세요"
        and selected_district_new != st_session_state.selected_district
    ):
        cache_manager.select_district(selected_district_new)
        cache_manager.clear_comparison_mode()
        st.rerun()

    # 선택된 자치구 정보 미리보기
    if st_session_state.selected_district:
        # 선택된 자치구의 기본 정보 표시
        district_row = gugun_ranking_df[
            gugun_ranking_df["gugun"] == st_session_state.selected_district
        ].iloc[0]
        district_rank = district_row.name + 1  # DataFrame 인덱스 기반
        district_price = district_row["price_84m2_manwon"]

        st.markdown(
            f"#### 🎯 선택된 기준 자치구: **{st_session_state.selected_district}**"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="🏆 서울시 순위",
                value=f"{district_rank}위",
                help="매매가 기준 서울시 내 순위",
            )
        with col2:
            price_str = fmt.format_price_eok(district_price)
            st.metric(label="🏠 평균 매매가", value=price_str, help="국평(84m²) 기준")

    # 비교 모드 선택 버튼
    if st_session_state.selected_district:
        st.markdown("#### 🔍 비교 방식 선택")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏘️ 인접 자치구 비교", use_container_width=True):
                cache_manager.set_comparison_mode("adjacent")
                st.rerun()

        with col2:
            if st.button("💰 유사 매매가 비교", use_container_width=True):
                cache_manager.set_comparison_mode("similar_price")
                st.rerun()

    # 비교 분석 결과 표시
    comparison_results = None
    if st_session_state.comparison_mode:
        _render_comparison_results(st_session_state, gugun_ranking_df, apt_price_df)

        # 비교 결과 데이터 수집 (컨텍스트용)
        try:
            if st_session_state.comparison_mode == "adjacent":
                comparison_results = spatial_analyzer.get_district_neighbors_info(
                    gugun_ranking_df, st_session_state.selected_district
                )
            elif st_session_state.comparison_mode == "similar_price":
                comparison_results = comparison_engine.find_similar_price_districts(
                    gugun_ranking_df, st_session_state.selected_district
                )
        except Exception:
            pass

    # 챗봇 영역 (맨 아래 배치)
    st.markdown("---")
    chat_action = chat_interface.render_chat_interface(
        st_session_state, latest_month, latest_avg_price, gugun_ranking_df
    )

    # 모드별 컨텍스트 생성
    context_data = {"mode": "comparison"}

    if st_session_state.selected_district:
        # 기준 자치구 정보
        district_info = gugun_ranking_df[
            gugun_ranking_df["gugun"] == st_session_state.selected_district
        ]

        if not district_info.empty:
            rank = district_info.index[0] + 1
            price = district_info["price_84m2_manwon"].iloc[0]

            context_data.update(
                {
                    "selected_district": st_session_state.selected_district,
                    "rank": rank,
                    "price": price,
                    "comparison_mode": st_session_state.comparison_mode,
                    "comparison_results": (
                        {
                            "count": (
                                len(comparison_results)
                                if comparison_results is not None
                                else 0
                            ),
                            "type": (
                                "인접 자치구"
                                if st_session_state.comparison_mode == "adjacent"
                                else "유사 매매가"
                            ),
                        }
                        if comparison_results is not None
                        else None
                    ),
                }
            )

    return context_data, chat_action


def _render_comparison_results(st_session_state, gugun_ranking_df, apt_price_df):
    """비교 분석 결과 렌더링 (내부 함수)"""
    if st_session_state.comparison_mode == "adjacent":
        st.success("📍 인접 자치구와 비교 분석을 시작합니다.")

        with st.spinner("🔍 인접 자치구를 분석하고 있습니다..."):
            neighbors_info = spatial_analyzer.get_district_neighbors_info(
                st_session_state.selected_district, gugun_ranking_df, apt_price_df
            )

        st.markdown("#### 📊 인접 자치구 비교 분석")
        st.info(neighbors_info["summary"])

        if not neighbors_info["comparison_data"].empty:
            # 컬럼 존재 여부 확인 후 안전하게 처리
            available_cols = neighbors_info["comparison_data"].columns.tolist()

            # 기본 컬럼 (항상 존재해야 함)
            select_cols = ["gugun", "price_84m2_manwon"]
            column_names = ["자치구", "국평(84m²) 매매가"]

            # 인접 자치구 전용 컬럼이 있는 경우만 추가
            if "avg_build_year" in available_cols:
                select_cols.append("avg_build_year")
                column_names.append("평균 건축년도")

            if "total_households" in available_cols:
                select_cols.append("total_households")
                column_names.append("총 세대수")

            comparison_df = neighbors_info["comparison_data"][select_cols].copy()

            # 매매가 포맷팅
            comparison_df["price_84m2_manwon"] = comparison_df[
                "price_84m2_manwon"
            ].apply(lambda x: f"{x:,.0f}만원")

            # 평균 건축년도 포맷팅 (존재할 때만)
            if "avg_build_year" in comparison_df.columns:
                comparison_df["avg_build_year"] = comparison_df["avg_build_year"].apply(
                    lambda x: f"{x:.0f}년" if pd.notna(x) else "N/A"
                )

            # 총 세대수 포맷팅 (존재할 때만)
            if "total_households" in comparison_df.columns:
                comparison_df["total_households"] = comparison_df[
                    "total_households"
                ].apply(lambda x: f"{x:,.0f}세대" if pd.notna(x) else "N/A")

            comparison_df.columns = column_names
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    elif st_session_state.comparison_mode == "similar_price":
        st.success("💰 유사 매매가 자치구와 비교 분석을 시작합니다.")

        with st.spinner("💰 유사 매매가 자치구를 분석하고 있습니다..."):
            similar_info = comparison_engine.find_similar_price_districts(
                st_session_state.selected_district, gugun_ranking_df, apt_price_df
            )

        st.markdown("#### 📊 유사 매매가 자치구 비교 분석")
        st.info(similar_info["summary"])

        if not similar_info["comparison_data"].empty:
            # 컬럼 존재 여부 확인 후 안전하게 처리
            available_cols = similar_info["comparison_data"].columns.tolist()

            # 기본 컬럼 (항상 존재해야 함)
            select_cols = ["gugun", "price_84m2_manwon"]
            column_names = ["자치구", "국평(84m²) 매매가"]

            # 유사 매매가 전용 컬럼이 있는 경우만 추가
            if "price_difference_pct" in available_cols:
                select_cols.append("price_difference_pct")
                column_names.append("가격차이(%)")

            if "similarity_score" in available_cols:
                select_cols.append("similarity_score")
                column_names.append("유사도점수")

            comparison_df = similar_info["comparison_data"][select_cols].copy()

            # 매매가 포맷팅
            comparison_df["price_84m2_manwon"] = comparison_df[
                "price_84m2_manwon"
            ].apply(lambda x: f"{x:,.0f}만원")

            # 가격차이% 포맷팅 (존재할 때만)
            if "price_difference_pct" in comparison_df.columns:
                comparison_df["price_difference_pct"] = comparison_df[
                    "price_difference_pct"
                ].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")

            # 유사도점수 포맷팅 (존재할 때만)
            if "similarity_score" in comparison_df.columns:
                comparison_df["similarity_score"] = comparison_df[
                    "similarity_score"
                ].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

            comparison_df.columns = column_names
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
