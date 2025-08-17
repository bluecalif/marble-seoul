#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""main.py
Marble서울 프로토타입 – 새로운 모드 기반 UI 구조 (단계 7)
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import os
from datetime import datetime

import streamlit as st
import pandas as pd

# --- 안전한 로깅 설정 ---
LOG_FILE = "marbleseoul/docs/session_logs/debug_log_20250817.txt"
if "log_initialized" not in st.session_state:
    # 로그 디렉토리 생성
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- Log Start: {datetime.now()} ---\n")
    st.session_state.log_initialized = True


def write_log(message: str):
    """시스템 임시 디렉토리에 로그를 기록합니다."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {message}\n")


# --- PYTHONPATH 세팅 (import 전에 먼저 설정!) ---
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- 모듈 import ---
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
from marbleseoul.ui import (
    layout,
    chat_interface,
    data_display,
    mode_renderer,
)
from marbleseoul.app import langchain_chat as lc
from marbleseoul.utils import formatters as fmt

# --- 페이지 설정 및 초기화 ---
write_log("=== NEW UI STRUCTURE START ===")
layout.configure_page()
cache_manager.init_session_state()

# 세션 상태 검증 및 복구
if not cache_manager.validate_session_state():
    write_log("Session state validation failed, attempting repair")
    cache_manager.repair_session_state()

write_log(f"Current mode: {st.session_state.view_stage}")
session_summary = cache_manager.get_session_state_summary()
write_log(f"Session state: {session_summary}")


# --- 데이터 로딩 ---
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


def _create_mode_specific_context(context_data, latest_month, latest_avg_price):
    """모드별 특화된 LLM 컨텍스트를 생성합니다."""
    if not context_data:
        # 기본 컨텍스트
        return f"2024년 12월 서울시 아파트 국평(84m²) 평균 매매가: {fmt.format_price_eok(latest_avg_price)}"

    mode = context_data.get("mode", "unknown")

    if mode == "overview":
        # 서울 전체 모드 컨텍스트
        highest = context_data["highest_district"]
        lowest = context_data["lowest_district"]
        top5 = ", ".join(context_data["top5_districts"])

        return f"""현재 모드: 서울 전체 현황
기준월: {latest_month}
서울시 전체 평균 매매가: {fmt.format_price_eok(context_data["seoul_avg_price"])}
총 자치구 수: {context_data["total_districts"]}개

🥇 최고가 자치구: {highest["name"]} ({fmt.format_price_eok(highest["price"])})
🏷️ 최저가 자치구: {lowest["name"]} ({fmt.format_price_eok(lowest["price"])})
📊 상위 5개 자치구: {top5}

사용자는 서울시 전체 현황을 보고 있으며, 전반적인 부동산 시장 동향에 대해 질문할 수 있습니다."""

    elif mode == "ranking":
        # 가격 5분위 모드 컨텍스트
        context = f"""현재 모드: 가격 5분위 분석
기준월: {latest_month}
총 분위 수: {context_data["total_quintiles"]}개 구간

5분위별 정보:"""

        for i, quintile in context_data["all_quintiles"].items():
            context += f"\n- {i}구간 ({quintile['label']}): {quintile['price_range']}, {quintile['count']}개 자치구"

        if context_data["selected_quintile"]:
            selected = context_data["selected_quintile"]
            context += f"\n\n현재 선택된 구간: {selected['quintile']}구간 ({selected['label']})"
            context += f"\n- 가격 범위: {selected['price_range']}"
            context += f"\n- 포함 자치구: {', '.join(selected['districts'])}"

        context += "\n\n사용자는 가격 분위별 자치구 분석을 보고 있으며, 특정 구간이나 가격대별 비교에 대해 질문할 수 있습니다."
        return context

    elif mode == "district":
        # 자치구 선택 모드 컨텍스트
        if "selected_district" in context_data:
            district = context_data["selected_district"]
            rank = context_data["rank"]
            price = context_data["price"]

            context = f"""현재 모드: 자치구 상세 분석
선택된 자치구: {district}
서울시 매매가 순위: {rank}위 (25개 자치구 중)
국평(84m²) 평균 매매가: {fmt.format_price_eok(price)}"""

            if context_data.get("apt_info"):
                apt_info = context_data["apt_info"]
                if apt_info.get("total_complexes"):
                    context += f"\n아파트 단지 수: {apt_info['total_complexes']}개"
                if apt_info.get("total_households"):
                    context += f"\n총 세대수: {apt_info['total_households']:,}세대"
                if apt_info.get("avg_build_year"):
                    context += f"\n평균 건축연도: {apt_info['avg_build_year']:.0f}년"
                if apt_info.get("min_price") and apt_info.get("max_price"):
                    context += f"\n가격 범위: {fmt.format_price_eok(apt_info['min_price'])} ~ {fmt.format_price_eok(apt_info['max_price'])}"

            context += f"\n\n사용자는 {district}의 상세 정보를 보고 있으며, 해당 자치구의 특성, 투자 가치, 주변 인프라 등에 대해 질문할 수 있습니다."
            return context
        else:
            return f"현재 모드: 자치구 선택\n아직 자치구가 선택되지 않았습니다. 사용자가 자치구를 선택하면 해당 자치구의 상세 분석을 제공할 수 있습니다."

    elif mode == "comparison":
        # 자치구 비교 모드 컨텍스트
        if "selected_district" in context_data:
            district = context_data["selected_district"]
            rank = context_data["rank"]
            price = context_data["price"]

            context = f"""현재 모드: 자치구 비교 분석
기준 자치구: {district}
기준 자치구 순위: {rank}위 (25개 자치구 중)
기준 자치구 매매가: {fmt.format_price_eok(price)}"""

            comparison_mode = context_data.get("comparison_mode")
            if comparison_mode and context_data.get("comparison_results"):
                results = context_data["comparison_results"]
                context += f"\n\n비교 방식: {results['type']}"
                context += f"\n비교 대상 수: {results['count']}개 자치구"

            context += f"\n\n사용자는 {district}을 기준으로 다른 자치구들과의 비교 분석을 보고 있으며, 유사한 특성의 자치구나 투자 대안에 대해 질문할 수 있습니다."
            return context
        else:
            return f"현재 모드: 자치구 비교\n기준 자치구가 선택되지 않았습니다. 자치구를 선택한 후 비교 분석을 진행할 수 있습니다."

    # 알 수 없는 모드
    return f"현재 모드: {mode}\n기본 서울시 아파트 정보를 제공합니다."


apt_price_df, latest_month, latest_avg_price, gugun_ranking_df, price_quintiles = (
    load_all_data()
)

# --- 초기 메시지 설정 ---
if not st.session_state.messages:
    year = latest_month // 100
    month = latest_month % 100
    price_str = fmt.format_price_eok(latest_avg_price)
    initial_msg = f"안녕하세요! 서울시 {year}년 {month}월 아파트 국평(84m²) 평균 매매가격은 **{price_str}**입니다."
    cache_manager.add_message("assistant", initial_msg)

    follow_up_msg = "🗺️ **모드 선택:**\n- **왼쪽 지도 상단의 모드 버튼**을 클릭하여 원하는 분석 모드를 선택하세요!\n- 각 모드별로 다른 분석 기능을 제공합니다."
    cache_manager.add_message("assistant", follow_up_msg)

# --- 비교 모드 데이터 사전 준비 ---
if (
    st.session_state.selected_district
    and st.session_state.comparison_mode
    and not st.session_state.comparison_districts
):
    if st.session_state.comparison_mode == "adjacent":
        neighbors_info = spatial_analyzer.get_district_neighbors_info(
            st.session_state.selected_district, gugun_ranking_df, apt_price_df
        )
        cache_manager.set_comparison_districts(neighbors_info["adjacent_districts"])
    elif st.session_state.comparison_mode == "similar_price":
        similar_info = comparison_engine.find_similar_price_districts(
            st.session_state.selected_district, gugun_ranking_df, apt_price_df
        )
        cache_manager.set_comparison_districts(similar_info["similar_districts"])

# --- UI 렌더링 ---
write_log("UI 렌더링 시작")
col_map, col_chat = st.columns([0.6, 0.4], gap="large")

# --- 왼쪽: 지도 영역 ---
with col_map:
    write_log("지도 컬럼 렌더링 시작")

    # 🎯 모드 선택 버튼 (상단)
    st.markdown("### 🗺️ 서울 지도")
    st.markdown("**분석 모드를 선택하세요:**")

    # 4개 모드 버튼을 2x2 그리드로 배치
    mode_col1, mode_col2 = st.columns(2)

    with mode_col1:
        if st.button(
            "🏢 서울 전체",
            use_container_width=True,
            type=(
                "primary" if st.session_state.view_stage == "overview" else "secondary"
            ),
        ):
            cache_manager.update_view_stage("overview")
            st.rerun()

        if st.button(
            "🏘️ 자치구 선택",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.view_stage == "district_selected"
                else "secondary"
            ),
        ):
            cache_manager.update_view_stage("district_selected")
            st.rerun()

    with mode_col2:
        if st.button(
            "📊 가격 5분위",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.view_stage == "gu_ranking"
                else "secondary"
            ),
        ):
            cache_manager.update_view_stage("gu_ranking")
            st.rerun()

        # 자치구 비교 버튼 (자치구 선택 시에만 활성화)
        comparison_disabled = not st.session_state.selected_district
        comparison_help = (
            "자치구를 먼저 선택해주세요"
            if comparison_disabled
            else "선택된 자치구와 다른 자치구들을 비교합니다"
        )

        if st.button(
            "⚖️ 자치구 비교",
            use_container_width=True,
            disabled=comparison_disabled,
            help=comparison_help,
            type=(
                "primary"
                if st.session_state.view_stage == "comparison"
                else "secondary"
            ),
        ):
            cache_manager.update_view_stage("comparison")
            st.rerun()

    st.markdown("---")

    # 모드별 지도 UI 렌더링
    map_action = None  # 기본값 초기화

    if st.session_state.view_stage == "overview":
        st.info(
            "🏢 **서울 전체 현황**을 표시합니다. 챗봇에서 서울 전체 정보를 질문해 보세요!"
        )

    elif st.session_state.view_stage == "gu_ranking":
        st.info(
            "📊 **가격 5분위 모드**입니다. 아래 구간 버튼을 클릭하여 해당 구간의 자치구들을 확인하세요!"
        )

    elif st.session_state.view_stage == "district_selected":
        st.info(
            "🏘️ **자치구 선택 모드**입니다. 지도에서 자치구를 클릭하거나 오른쪽 챗봇에서 풀다운으로 선택하세요!"
        )

    elif st.session_state.view_stage == "comparison":
        st.info(
            "⚖️ **자치구 비교 모드**입니다. 오른쪽에서 자치구를 선택하고 비교 방식을 선택하세요!"
        )

    # URL 파라미터 처리 (자치구 선택 관련 모드에서만)
    if st.session_state.view_stage in ["district_selected", "comparison"]:
        query_params = st.query_params
        if "map_selected_district" in query_params:
            clicked_district = query_params["map_selected_district"]
            if clicked_district != st.session_state.selected_district:
                cache_manager.select_district(clicked_district)
                cache_manager.clear_comparison_mode()

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

                del st.query_params["map_selected_district"]
                st.rerun()

    # 지도 렌더링
    write_log("map_manager 렌더링 시작")
    display_map_action = map_manager.display_map(
        st.session_state,
        latest_month,
        latest_avg_price,
        gugun_ranking_df,
        price_quintiles,
    )

    # 지도에서 반환된 액션을 map_action에 할당
    if display_map_action:
        map_action = display_map_action

    write_log("지도 컬럼 렌더링 완료")

# --- 오른쪽: 챗봇 영역 ---
with col_chat:
    write_log("채팅 컬럼 렌더링 시작")

    # 모드별 UI 렌더링 (mode_renderer 모듈 사용)
    context_data = None

    if st.session_state.view_stage == "overview":
        context_data, chat_action = mode_renderer.render_overview_mode(
            st.session_state, latest_month, latest_avg_price, gugun_ranking_df
        )

    elif st.session_state.view_stage == "gu_ranking":
        context_data, chat_action = mode_renderer.render_ranking_mode(
            st.session_state,
            latest_month,
            latest_avg_price,
            gugun_ranking_df,
            price_quintiles,
        )

    elif st.session_state.view_stage == "district_selected":
        context_data, chat_action = mode_renderer.render_district_mode(
            st.session_state,
            latest_month,
            latest_avg_price,
            gugun_ranking_df,
            apt_price_df,
        )

    elif st.session_state.view_stage == "comparison":
        context_data, chat_action = mode_renderer.render_comparison_mode(
            st.session_state,
            latest_month,
            latest_avg_price,
            gugun_ranking_df,
            apt_price_df,
        )
    else:
        # 기본값 (예외 처리)
        context_data = None
        chat_action = None

    write_log("채팅 컬럼 렌더링 완료")

# --- 액션 처리 ---
write_log("액션 처리 시작")
needs_rerun = False

# 지도 액션 처리
if "map_action" in locals() and map_action:
    action_type, action_data = map_action
    write_log(f"Map action: {action_type}, {action_data}")

    if action_type == "quintile_selected":
        quintile = action_data
        cache_manager.select_quintile(quintile)

        if quintile is not None:
            # price_quintiles는 딕셔너리 구조이므로 직접 접근
            quintile_data = price_quintiles[quintile]
            district_names = quintile_data["gus"]
            district_count = len(district_names)

            min_price_str = fmt.format_price_eok(quintile_data["price_min"])
            max_price_str = fmt.format_price_eok(quintile_data["price_max"])

            quintile_msg = (
                f"**{quintile}구간**이 선택되었습니다!\n\n"
                f"- **가격 범위**: {min_price_str} ~ {max_price_str}\n"
                f"- **포함 자치구**: {district_count}개\n"
                f"- **자치구 목록**: {', '.join(district_names[:3])}"
                + (f" 외 {district_count-3}개" if district_count > 3 else "")
                + f"\n\n이 구간에 대해 더 자세히 알고 싶으시다면 질문해 보세요!"
            )
        else:
            quintile_msg = (
                "가격 구간 선택이 해제되었습니다. 전체 서울시 현황으로 돌아갑니다."
            )

        cache_manager.add_message("assistant", quintile_msg)
        needs_rerun = True

# 챗봇 액션 처리
write_log(f"🔍 CHECKING CHAT ACTION: chat_action={'chat_action' in locals()}")
if "chat_action" in locals():
    write_log(f"📋 CHAT ACTION VALUE: {chat_action}")

if "chat_action" in locals() and chat_action:
    # 딕셔너리 형태의 chat_action 파싱
    if isinstance(chat_action, dict):
        action_type = chat_action.get('type')
        action_data = chat_action.get('data')
    else:
        action_type, action_data = chat_action
    write_log(f"📨 PROCESSING CHAT ACTION: {action_type}, {action_data}")

    if action_type == "ranking_requested":
        cache_manager.update_view_stage("gu_ranking")
        cache_manager.set_ranking_df(gugun_ranking_df)

        ranking_msg = (
            f"📊 서울시 25개 자치구의 아파트 매매가 랭킹을 표시했습니다.\n\n"
            f"왼쪽 지도에서 **가격 구간 버튼**을 클릭하면 해당 구간의 자치구들이 강조됩니다. "
            f"이 지역에 대해 무엇이 궁금하신가요?"
        )
        cache_manager.add_message("assistant", ranking_msg)
        needs_rerun = True

    elif action_type == "back_to_overview":
        cache_manager.update_view_stage("overview")
        cache_manager.clear_ranking_df()

        overview_msg = (
            f"🏢 서울 전체 현황으로 돌아왔습니다.\n\n"
            f"다시 자치구별 랭킹을 보시려면 **'랭킹'**을 입력해 주세요."
        )
        cache_manager.add_message("assistant", overview_msg)
        needs_rerun = True

    elif action_type == "chat":
        write_log(f"🤖 CHAT ACTION DETECTED: {action_data}")

        # 모드별 특화 컨텍스트 생성
        context = _create_mode_specific_context(
            context_data, latest_month, latest_avg_price
        )
        write_log(
            f"🔧 CONTEXT CREATED: {context[:100]}..." if context else "⚠️ NO CONTEXT"
        )

        try:
            write_log("🔄 CALLING LLM...")
            response = lc.predict(action_data, context)
            write_log(
                f"✅ LLM RESPONSE: {response[:100]}..."
                if response
                else "⚠️ EMPTY RESPONSE"
            )

            cache_manager.add_message("user", action_data)
            cache_manager.add_message("assistant", response)
            write_log("💾 MESSAGES ADDED TO CACHE")
            needs_rerun = True

        except Exception as e:
            write_log(f"❌ LLM ERROR: {str(e)}")
            response = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
            cache_manager.add_message("user", action_data)
            cache_manager.add_message("assistant", response)
            needs_rerun = True

if needs_rerun:
    write_log("!!! st.rerun() CALLED !!!")
    st.rerun()
