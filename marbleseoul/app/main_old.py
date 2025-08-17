#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""main.py
Marble서울 프로토타입 – Streamlit 메인 애플리케이션 (단계 4 테스트)
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import os
from datetime import datetime

import streamlit as st
import pandas as pd

# --- 안전한 로깅 설정 (Streamlit 감시 범위 외부) ---
LOG_FILE = os.path.join(tempfile.gettempdir(), "marble_debug_log.txt")
if "log_initialized" not in st.session_state:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- Log Start: {datetime.now()} ---\n")
    st.session_state.log_initialized = True


def write_log(message: str):
    """시스템 임시 디렉토리에 로그를 기록합니다."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {message}\n")


from marbleseoul.core import cache_manager, map_manager
from marbleseoul.data import (
    loaders,
    processors,
    rankings,
    district_analyzer,
    spatial_analyzer,
    comparison_engine,
    visualization,
)
from marbleseoul.ui import layout, map_controls, chat_interface, data_display
from marbleseoul.app import langchain_chat as lc
from marbleseoul.utils import formatters as fmt
from marbleseoul.core import map_manager, cache_manager
from marbleseoul.data import loaders, district_analyzer
from marbleseoul.ui import data_display
from marbleseoul.data import dong_analyzer


# --- PYTHONPATH 세팅 ---------------------------------------------------------
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- 페이지 설정 및 초기화 ---
write_log("=== SCRIPT START ===")
layout.configure_page()
cache_manager.init_session_state()
write_log(f"view_stage: {st.session_state.view_stage}")


# --- 데이터 로딩 (캐싱 활용) ---
@st.cache_data
def load_all_data():
    apt_price_df = loaders.load_apt_price_data()
    _, latest_month, latest_avg_price = processors.process_monthly_avg(apt_price_df)
    gugun_ranking_df = rankings.calculate_gugun_ranking(apt_price_df, latest_month)
    price_quintiles = rankings.calculate_price_quintiles(gugun_ranking_df)
    return (
        apt_price_df,
        latest_month,
        latest_avg_price,
        gugun_ranking_df,
        price_quintiles,
    )


apt_price_df, latest_month, latest_avg_price, gugun_ranking_df, price_quintiles = (
    load_all_data()
)

# --- 초기 메시지 설정 (최초 1회만 실행) ---
if not st.session_state.messages:
    year = latest_month // 100
    month = latest_month % 100
    price_str = fmt.format_price_eok(latest_avg_price)
    initial_msg = f"안녕하세요! 서울시 {year}년 {month}월 아파트 국평(84m²) 평균 매매가격은 **{price_str}**입니다."
    cache_manager.add_message("assistant", initial_msg)
    follow_up_msg = "🗺️ **지도 모드 안내:**\n- **현재**: 서울 전체 현황 표시\n- **'랭킹' 입력**: 자치구별 상세 비교 모드로 전환\n- **'전체' 입력**: 다시 전체 현황 모드로 복귀\n\n자치구별 랭킹을 보시겠습니까?"
    cache_manager.add_message("assistant", follow_up_msg)

# --- 비교 모드 데이터 사전 준비 ---
if (
    st.session_state.selected_district
    and st.session_state.comparison_mode
    and not st.session_state.comparison_districts
):
    if st.session_state.comparison_mode == "adjacent":
        # 인접 자치구 분석을 지도 렌더링 전에 수행
        neighbors_info = spatial_analyzer.get_district_neighbors_info(
            st.session_state.selected_district, gugun_ranking_df, apt_price_df
        )
        cache_manager.set_comparison_districts(neighbors_info["adjacent_districts"])

    elif st.session_state.comparison_mode == "similar_price":
        # 유사 매매가 자치구 분석을 지도 렌더링 전에 수행
        similar_info = comparison_engine.find_similar_price_districts(
            st.session_state.selected_district, gugun_ranking_df, apt_price_df
        )
        cache_manager.set_comparison_districts(similar_info["similar_districts"])

# --- UI 렌더링 및 사용자 액션 수집 ---
write_log("UI 렌더링 시작")
col_map, col_chat = st.columns([0.6, 0.4], gap="large")
map_action = None
chat_action = None

with col_map:
    write_log("지도 컬럼 렌더링 시작")
    
    # 🎯 모드 선택 버튼 추가 (상단)
    st.markdown("### 🗺️ 서울 지도")
    st.markdown("**분석 모드를 선택하세요:**")
    
    # 4개 모드 버튼을 2x2 그리드로 배치
    mode_col1, mode_col2 = st.columns(2)
    
    with mode_col1:
        if st.button("🏢 서울 전체", use_container_width=True, 
                    type="primary" if st.session_state.view_stage == "overview" else "secondary"):
            cache_manager.update_view_stage("overview")
            st.rerun()
            
        if st.button("🏘️ 자치구 선택", use_container_width=True,
                    type="primary" if st.session_state.view_stage == "district_selected" else "secondary"):
            cache_manager.update_view_stage("district_selected")
            st.rerun()
    
    with mode_col2:
        if st.button("📊 가격 5분위", use_container_width=True,
                    type="primary" if st.session_state.view_stage == "gu_ranking" else "secondary"):
            cache_manager.update_view_stage("gu_ranking")
            st.rerun()
            
        if st.button("⚖️ 자치구 비교", use_container_width=True,
                    type="primary" if st.session_state.view_stage == "comparison" else "secondary"):
            cache_manager.update_view_stage("comparison")
            st.rerun()
    
    st.markdown("---")
    
    # 🔧 지도 영역 - 높이 자동 조정으로 프레임 문제 해결
    map_container = st.container()
    with map_container:
        # 모드별 지도 UI 렌더링
        if st.session_state.view_stage == "overview":
            st.info("🏢 **서울 전체 현황**을 표시합니다. 챗봇에서 서울 전체 정보를 질문해 보세요!")
            
        elif st.session_state.view_stage == "gu_ranking":
            st.info("📊 **가격 5분위 모드**입니다. 아래 구간 버튼을 클릭하여 해당 구간의 자치구들을 확인하세요!")
            # 디버깅용 JavaScript (콘솔 로그 확인용)
            js_code = """
            <script>
            console.log('지도 클릭 기능 활성화됨 - 버튼 클릭 시 console.log 확인 가능');
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
            write_log("랭킹 모드: map_controls 렌더링")
            map_action = map_controls.render_map_controls(
                st.session_state, price_quintiles
            )
            
        elif st.session_state.view_stage == "district_selected":
            st.info("🏘️ **자치구 선택 모드**입니다. 지도에서 자치구를 클릭하거나 오른쪽 챗봇에서 풀다운으로 선택하세요!")
            
        elif st.session_state.view_stage == "comparison":
            st.info("⚖️ **자치구 비교 모드**입니다. 오른쪽에서 자치구를 선택하고 비교 방식을 선택하세요!")

        # URL 파라미터에서 지도 클릭으로 선택된 자치구 확인 (자치구 선택 관련 모드에서만)
        if st.session_state.view_stage in ["district_selected", "comparison"]:
            query_params = st.query_params
            if "map_selected_district" in query_params:
                clicked_district = query_params["map_selected_district"]
                if clicked_district != st.session_state.selected_district:
                    # 지도에서 새로운 자치구가 클릭되었을 때
                    cache_manager.select_district(clicked_district)
                    cache_manager.clear_comparison_mode()

                    # 자치구 선택 성공 메시지 추가
                    district_info_new = gugun_ranking_df[
                        gugun_ranking_df["gugun"] == clicked_district
                    ]
                    if not district_info_new.empty:
                        rank = district_info_new.index[0] + 1
                        price = district_info_new["price_84m2_manwon"].iloc[0]
                        price_str = fmt.format_price_eok(price)

                        click_msg = (
                            f"🗺️ **{clicked_district}**을(를) 지도에서 선택하셨습니다!\n\n"
                            f"- **서울시 매매가 순위**: **{rank}위**\n"
                            f"- **국평(84m²) 평균 매매가**: **{price_str}**"
                        )
                        cache_manager.add_message("assistant", click_msg)

                    # URL 파라미터 정리
                    del st.query_params["map_selected_district"]
                    st.rerun()

    write_log("map_manager 렌더링 시작")
    display_map_action = map_manager.display_map(
        st.session_state,
        latest_month,
        latest_avg_price,
        gugun_ranking_df,
        price_quintiles,
    )
    write_log("지도 컬럼 렌더링 완료")
    # 지도 컨테이너는 자동으로 닫힘 (Streamlit Container)

with col_chat:
    write_log("채팅 컬럼 렌더링 시작")

    # 🎯 모드별 챗봇 UI 렌더링
    if st.session_state.view_stage == "overview":
        # 서울 전체 모드: 기본 챗봇 인터페이스
        chat_action = chat_interface.render_chat_interface(
            st.session_state, latest_month, latest_avg_price, gugun_ranking_df
        )
        
    elif st.session_state.view_stage == "gu_ranking":
        # 가격 5분위 모드: 랭킹 테이블 + 자치구 선택
        chat_action = chat_interface.render_chat_interface(
            st.session_state, latest_month, latest_avg_price, gugun_ranking_df
        )
        
    elif st.session_state.view_stage == "district_selected":
        # 자치구 선택 모드: 자치구 선택 풀다운
        chat_action = chat_interface.render_chat_interface(
            st.session_state, latest_month, latest_avg_price, gugun_ranking_df
        )
        
        # 자치구 선택 풀다운
        all_districts = ["자치구를 선택하세요"] + sorted(gugun_ranking_df["gugun"].tolist())
        
        if st.session_state.selected_district:
            st.markdown("#### 🎯 선택된 자치구")
            try:
                current_index = all_districts.index(st.session_state.selected_district)
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
        if (selected_district_new != "자치구를 선택하세요" and 
            selected_district_new != st.session_state.selected_district):
            cache_manager.select_district(selected_district_new)
            
            # 새로운 자치구 선택 메시지 추가
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
        if st.session_state.selected_district:
            district_info = district_analyzer.get_district_apartment_info(
                apt_price_df, st.session_state.selected_district
            )
            data_display.display_district_info(district_info)
            
    elif st.session_state.view_stage == "comparison":
        # 자치구 비교 모드
        chat_action = chat_interface.render_chat_interface(
            st.session_state, latest_month, latest_avg_price, gugun_ranking_df
        )
        
        # 자치구 선택 풀다운
        all_districts = ["자치구를 선택하세요"] + sorted(gugun_ranking_df["gugun"].tolist())
        
        if st.session_state.selected_district:
            current_index = all_districts.index(st.session_state.selected_district)
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
        if (selected_district_new != "자치구를 선택하세요" and 
            selected_district_new != st.session_state.selected_district):
            cache_manager.select_district(selected_district_new)
            cache_manager.clear_comparison_mode()
            st.rerun()
            
        # 비교 모드 선택 버튼
        if st.session_state.selected_district:
            st.markdown("#### 🔍 비교 방식 선택")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏘️ 인접 자치구 비교", use_container_width=True):
                    cache_manager.set_comparison_mode("adjacent")
                    st.cache_data.clear()
                    st.rerun()

            with col2:
                if st.button("💰 유사 매매가 비교", use_container_width=True):
                    cache_manager.set_comparison_mode("similar_price")
                    st.rerun()

    # 비교 모드에서 비교 분석 결과 표시
    if st.session_state.view_stage == "comparison" and st.session_state.comparison_mode:

                # 비교 모드가 선택되었을 때 분석 수행
        if st.session_state.comparison_mode:
            if st.session_state.comparison_mode == "adjacent":
                st.success("📍 인접 자치구와 비교 분석을 시작합니다.")

                # 인접 자치구 분석 수행 (이미 수행되었다면 스킵)
                if not st.session_state.comparison_districts:
                    with st.spinner("🔍 인접 자치구를 분석하고 있습니다..."):
                        neighbors_info = spatial_analyzer.get_district_neighbors_info(
                            st.session_state.selected_district,
                            gugun_ranking_df,
                            apt_price_df,
                        )
                        cache_manager.set_comparison_districts(
                            neighbors_info["adjacent_districts"]
                        )
                else:
                    # 이미 분석된 데이터 사용
                    neighbors_info = spatial_analyzer.get_district_neighbors_info(
                        st.session_state.selected_district,
                        gugun_ranking_df,
                        apt_price_df,
                    )

                # 분석 결과 표시
                st.markdown("#### 📊 인접 자치구 비교 분석")
                st.info(neighbors_info["summary"])

                if not neighbors_info["comparison_data"].empty:
                    # 비교 데이터 테이블 표시 (매매가, 연식, 세대수 포함)
                    comparison_df = neighbors_info["comparison_data"][
                        [
                            "gugun",
                            "price_84m2_manwon",
                            "avg_build_year",
                            "total_households",
                        ]
                    ].copy()

                    # 데이터 포맷팅
                    comparison_df["price_84m2_manwon"] = comparison_df[
                        "price_84m2_manwon"
                    ].apply(lambda x: f"{x:,.0f}만원")
                    comparison_df["avg_build_year"] = comparison_df[
                        "avg_build_year"
                    ].apply(lambda x: f"{x:.0f}년" if pd.notna(x) else "N/A")
                    comparison_df["total_households"] = comparison_df[
                        "total_households"
                    ].apply(lambda x: f"{x:,.0f}세대" if pd.notna(x) else "N/A")

                    comparison_df.columns = [
                        "자치구",
                        "국평(84m²) 매매가",
                        "평균 건축년도",
                        "총 세대수",
                    ]

                    st.dataframe(
                        comparison_df, use_container_width=True, hide_index=True
                    )

                    # 비교 그래프 생성 및 표시
                    st.markdown("#### 📊 인접 자치구 비교 그래프")

                    with st.spinner("📈 비교 그래프를 생성하고 있습니다..."):
                        charts = visualization.generate_all_comparison_charts(
                            neighbors_info["comparison_data"],
                            st.session_state.selected_district,
                            "adjacent",
                        )

                    if charts:
                        # 탭으로 차트 구분 표시
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(
                            [
                                "💰 매매가격",
                                "🏗️ 건축년도",
                                "📈 종합비교",
                                "🏠 세대수",
                                "👥 인구vs매출",
                            ]
                        )

                        with tab1:
                            if "price" in charts:
                                st.plotly_chart(
                                    charts["price"], use_container_width=True
                                )

                        with tab2:
                            if "build_year" in charts:
                                st.plotly_chart(
                                    charts["build_year"], use_container_width=True
                                )

                        with tab3:
                            if "dual_axis" in charts:
                                st.plotly_chart(
                                    charts["dual_axis"], use_container_width=True
                                )

                        with tab4:
                            if "households" in charts:
                                st.plotly_chart(
                                    charts["households"], use_container_width=True
                                )

                        with tab5:
                            # 인구/매출 이중축 차트
                            with st.spinner(
                                "📊 인구 및 매출 데이터를 분석하고 있습니다..."
                            ):
                                pop_sales_chart = (
                                    visualization.generate_population_sales_chart(
                                        neighbors_info["adjacent_districts"],
                                        st.session_state.selected_district,
                                        "adjacent",
                                    )
                                )
                                st.plotly_chart(
                                    pop_sales_chart, use_container_width=True
                                )

                    # 세션 상태에 비교 자치구 저장 (이미 상단에서 처리됨)

            elif st.session_state.comparison_mode == "similar_price":
                st.success("💸 유사한 매매가 자치구들과 비교 분석을 시작합니다.")

                # 유사 매매가 자치구 분석 수행 (이미 수행되었다면 스킵)
                if not st.session_state.comparison_districts:
                    with st.spinner("💰 유사한 가격대의 자치구를 분석하고 있습니다..."):
                        similar_info = comparison_engine.find_similar_price_districts(
                            st.session_state.selected_district,
                            gugun_ranking_df,
                            apt_price_df,
                        )
                        cache_manager.set_comparison_districts(
                            similar_info["similar_districts"]
                        )
                else:
                    # 이미 분석된 데이터 사용
                    similar_info = comparison_engine.find_similar_price_districts(
                        st.session_state.selected_district,
                        gugun_ranking_df,
                        apt_price_df,
                    )

                # 분석 결과 표시
                st.markdown("#### 💰 유사 매매가 자치구 비교 분석")
                st.info(similar_info["summary"])

                # 비교 테이블 데이터 준비
                if not similar_info["comparison_data"].empty:
                    comparison_df = similar_info["comparison_data"][
                        [
                            "gugun",
                            "price_84m2_manwon",
                            "price_diff_pct",
                            "similarity_score",
                            "avg_build_year",
                            "total_households",
                        ]
                    ].copy()

                    # 컬럼명 한글화 및 포맷팅
                    comparison_df.columns = [
                        "자치구",
                        "84m² 매매가",
                        "가격차이(%)",
                        "유사도점수",
                        "평균 건축년도",
                        "총 세대수",
                    ]

                    # 데이터 포맷팅
                    comparison_df["84m² 매매가"] = comparison_df["84m² 매매가"].apply(
                        lambda x: f"₩{x:,.0f}만원"
                    )
                    comparison_df["가격차이(%)"] = comparison_df["가격차이(%)"].apply(
                        lambda x: f"{x:+.1f}%" if abs(x) > 0.1 else "기준"
                    )
                    comparison_df["유사도점수"] = comparison_df["유사도점수"].apply(
                        lambda x: f"{x:.1f}점"
                    )
                    comparison_df["평균 건축년도"] = comparison_df[
                        "평균 건축년도"
                    ].apply(lambda x: f"{x:.0f}년" if pd.notna(x) else "N/A")
                    comparison_df["총 세대수"] = comparison_df["총 세대수"].apply(
                        lambda x: f"{x:,.0f}세대" if pd.notna(x) else "N/A"
                    )

                    st.dataframe(
                        comparison_df, use_container_width=True, hide_index=True
                    )

                    # 비교 그래프 생성 및 표시
                    st.markdown("#### 📊 유사 매매가 자치구 비교 그래프")

                    with st.spinner("📈 비교 그래프를 생성하고 있습니다..."):
                        charts = visualization.generate_all_comparison_charts(
                            similar_info["comparison_data"],
                            st.session_state.selected_district,
                            "similar_price",
                        )

                    if charts:
                        # 탭으로 차트 구분 표시
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(
                            [
                                "💰 매매가격",
                                "🏗️ 건축년도",
                                "📈 종합비교",
                                "🏠 세대수",
                                "👥 인구vs매출",
                            ]
                        )

                        with tab1:
                            if "price" in charts:
                                st.plotly_chart(
                                    charts["price"], use_container_width=True
                                )

                        with tab2:
                            if "build_year" in charts:
                                st.plotly_chart(
                                    charts["build_year"], use_container_width=True
                                )

                        with tab3:
                            if "dual_axis" in charts:
                                st.plotly_chart(
                                    charts["dual_axis"], use_container_width=True
                                )

                        with tab4:
                            if "households" in charts:
                                st.plotly_chart(
                                    charts["households"], use_container_width=True
                                )

                        with tab5:
                            # 인구/매출 이중축 차트
                            with st.spinner(
                                "📊 인구 및 매출 데이터를 분석하고 있습니다..."
                            ):
                                pop_sales_chart = (
                                    visualization.generate_population_sales_chart(
                                        similar_info["similar_districts"],
                                        st.session_state.selected_district,
                                        "similar_price",
                                    )
                                )
                                st.plotly_chart(
                                    pop_sales_chart, use_container_width=True
                                )

                    # 세션 상태에 비교 자치구 저장 (이미 상단에서 처리됨)

            # 비교 모드 해제 버튼
            if st.button("❌ 비교 모드 해제"):
                cache_manager.clear_comparison_mode()
                # 지도 캐시 무효화 (기본 색상으로 복원)
                st.cache_data.clear()
                st.rerun()

        # 행정동 드롭다운 추가 (비교 모드가 아닐 때만 표시)
        if not st.session_state.comparison_mode:
            st.markdown("---")
            st.markdown("##### 🏠 행정동별 상세 분석")

            # 선택된 자치구의 행정동 목록 추출
            district_data = apt_price_df[
                apt_price_df["gugun"] == st.session_state.selected_district
            ]
            if not district_data.empty:
                dong_list = ["행정동을 선택하세요"] + sorted(
                    district_data["dong"].unique().tolist()
                )
                selected_dong = st.selectbox(
                    f"{st.session_state.selected_district}의 행정동을 선택해주세요:",
                    dong_list,
                    key="dong_selector",
                )

                # 행정동이 선택되었을 때 상세 정보 표시
                if selected_dong != "행정동을 선택하세요":
                    dong_info = dong_analyzer.get_dong_apartment_info(
                        apt_price_df, st.session_state.selected_district, selected_dong
                    )
                    if dong_info:
                        data_display.display_dong_info(dong_info)
                    else:
                        st.warning(f"{selected_dong}에 대한 아파트 데이터가 없습니다.")
            else:
                st.warning(
                    f"{st.session_state.selected_district}에 대한 데이터를 찾을 수 없습니다."
                )

    write_log("채팅 컬럼 렌더링 완료")
    # 챗봇 영역 렌더링 완료

write_log(f"UI 렌더링 완료, map_action: {map_action}, chat_action: {chat_action}")

# --- 중앙 집중식 상태 처리 ---
needs_rerun = False

# 지도 액션 처리
if display_map_action:
    write_log(f">>> display_map_action: {display_map_action}")
    if display_map_action["type"] == "refresh_map":
        needs_rerun = True

if chat_action:
    write_log(f">>> chat_action: {chat_action}")
    action_type = chat_action.get("type")
    action_data = chat_action.get("data")

    # 모든 사용자 입력은 먼저 메시지로 추가
    if action_data:
        cache_manager.add_message("user", action_data)

    if action_type == "show_ranking":
        cache_manager.update_view_stage("gu_ranking")
        display_df = fmt.format_gugun_ranking_df(gugun_ranking_df, price_quintiles)
        cache_manager.set_ranking_df(display_df)
        cache_manager.add_message(
            "assistant",
            "🏆 자치구별 랭킹 모드로 변경되었습니다. 이제 자치구를 선택하거나 추가 질문을 해주세요.",
        )
        needs_rerun = True
    elif action_type == "reset_view":
        cache_manager.update_view_stage("overview")
        cache_manager.clear_ranking_df()
        # 선택된 자치구 상태도 초기화하여 지도가 서울 전체로 복귀하도록 함
        cache_manager.clear_selected_district()
        # 비교 모드도 초기화
        cache_manager.clear_comparison_mode()
        cache_manager.add_message(
            "assistant", "🏙️ 서울 전체 현황 모드로 변경되었습니다."
        )
        needs_rerun = True
    elif action_type == "district_selected":
        cache_manager.select_district(action_data)
        # 새로운 자치구 선택 시 이전 비교 모드 초기화
        cache_manager.clear_comparison_mode()

        # 선택된 자치구의 상세 정보 생성
        district_info = gugun_ranking_df[gugun_ranking_df["gugun"] == action_data]
        if not district_info.empty:
            rank = district_info.index[0]
            price = district_info["price_84m2_manwon"].iloc[0]
            price_str = fmt.format_price_eok(price)

            summary_msg = (
                f"🎯 **{action_data}**을(를) 선택하셨습니다.\n\n"
                f"- **서울시 매매가 순위**: **{rank}위**\n"
                f"- **국평(84m²) 평균 매매가**: **{price_str}**\n\n"
                f"이 지역에 대해 무엇이 궁금하신가요?"
            )
        else:
            summary_msg = f"**{action_data}**이(가) 선택되었습니다. 이제 이 자치구에 대해 질문해보세요."

        cache_manager.add_message("assistant", summary_msg)
        needs_rerun = True
    elif action_type == "chat":
        # 선택된 자치구가 있을 경우 상세한 컨텍스트 제공
        if st.session_state.selected_district:
            district_info = gugun_ranking_df[
                gugun_ranking_df["gugun"] == st.session_state.selected_district
            ]
            if not district_info.empty:
                rank = district_info.index[0] + 1  # 1-based ranking
                price = district_info["price_84m2_manwon"].iloc[0]
                price_str = fmt.format_price_eok(price)

                # 자치구별 아파트 상세 정보 추가
                apt_info = district_analyzer.get_district_apartment_info(
                    apt_price_df, st.session_state.selected_district
                )

                context = (
                    f"현재 사용자가 선택한 자치구: {st.session_state.selected_district}\n"
                    f"- 서울시 매매가 순위: {rank}위\n"
                    f"- 국평(84m²) 평균 매매가: {price_str}\n"
                    f"- 총 아파트 단지 수: {apt_info['summary']['총 단지 수']}개\n"
                    f"- 평균 건축년도: {apt_info['summary']['평균 건축년도']:.0f}년\n"
                    f"- 최고 매매가: {apt_info['summary']['최고 매매가(84m²)']:,.0f}만원\n"
                    f"- 최저 매매가: {apt_info['summary']['최저 매매가(84m²)']:,.0f}만원\n"
                    f"- 총 세대수: {apt_info['summary']['총 세대수']:,.0f}세대\n\n"
                    f"위 정보를 바탕으로 {st.session_state.selected_district}에 대한 질문에 답변해주세요."
                )

            else:
                context = (
                    f"현재 선택된 자치구는 {st.session_state.selected_district}입니다."
                )
        else:
            context = "현재 서울 전체 모드입니다. 자치구를 선택하면 더 구체적인 정보를 제공할 수 있습니다."

        llm_resp = lc.predict(action_data, context=context)
        cache_manager.add_message("assistant", llm_resp)
        needs_rerun = True

elif map_action:
    write_log(f">>> map_action: {map_action}")
    if map_action["type"] == "select_quintile":
        cache_manager.select_quintile(map_action["data"])
        needs_rerun = True

if needs_rerun:
    write_log("!!! st.rerun() CALLED !!!")
    st.rerun()
