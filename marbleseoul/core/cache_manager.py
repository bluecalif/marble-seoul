#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cache_manager.py
Streamlit 세션 상태 및 지도 캐시 관리
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import importlib
import logging
from datetime import datetime

# --- 로깅 설정 ---
logger = logging.getLogger(__name__)

# 유효한 view_stage 값들
VALID_VIEW_STAGES = ["overview", "gu_ranking", "district_selected", "comparison"]

# 유효한 comparison_mode 값들
VALID_COMPARISON_MODES = [None, "adjacent", "similar_price"]


def init_session_state():
    """세션 상태를 초기화합니다."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "map_html" not in st.session_state:
        st.session_state.map_html = None
    if "ranking_df" not in st.session_state:
        st.session_state.ranking_df = None
    if "view_stage" not in st.session_state:
        st.session_state.view_stage = (
            "overview"  # overview, gu_ranking, district_selected, comparison
        )
    if "selected_district" not in st.session_state:
        st.session_state.selected_district = None
    if "selected_quintile" not in st.session_state:
        st.session_state.selected_quintile = None
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    # 비교 모드 관련 상태 초기화
    if "comparison_mode" not in st.session_state:
        st.session_state.comparison_mode = None  # None, "adjacent", "similar_price"
    if "comparison_districts" not in st.session_state:
        st.session_state.comparison_districts = []


# --- 상태 검증 함수 ---


def validate_view_stage(stage: str) -> bool:
    """view_stage 값의 유효성을 검증합니다."""
    return stage in VALID_VIEW_STAGES


def validate_comparison_mode(mode: str | None) -> bool:
    """comparison_mode 값의 유효성을 검증합니다."""
    return mode in VALID_COMPARISON_MODES


def validate_session_state() -> bool:
    """현재 세션 상태의 일관성을 검증합니다."""
    try:
        # 필수 상태 값들이 존재하는지 확인
        required_keys = ["view_stage", "selected_district", "comparison_mode"]
        for key in required_keys:
            if key not in st.session_state:
                logger.warning(f"Missing required session state key: {key}")
                return False

        # view_stage 유효성 검증
        if not validate_view_stage(st.session_state.view_stage):
            logger.warning(f"Invalid view_stage: {st.session_state.view_stage}")
            return False

        # comparison_mode 유효성 검증
        if not validate_comparison_mode(st.session_state.comparison_mode):
            logger.warning(
                f"Invalid comparison_mode: {st.session_state.comparison_mode}"
            )
            return False

        # 비교 모드인데 자치구가 선택되지 않은 경우
        if (
            st.session_state.view_stage == "comparison"
            and not st.session_state.selected_district
        ):
            logger.warning("Comparison mode without selected district")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating session state: {e}")
        return False


def log_state_change(operation: str, old_value=None, new_value=None):
    """상태 변경을 로깅합니다."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")
    if old_value != new_value:
        logger.info(f"[{timestamp}] {operation}: {old_value} -> {new_value}")


# --- 상태 변경 메소드 ---


def update_view_stage(stage: str):
    """뷰 상태를 변경하고 관련 상태를 정리합니다."""
    if not validate_view_stage(stage):
        logger.error(f"Invalid view_stage: {stage}")
        return False

    old_stage = st.session_state.get("view_stage")
    log_state_change("update_view_stage", old_stage, stage)

    st.session_state.view_stage = stage

    # 모드별 상태 정리
    if stage == "overview":
        # 서울 전체 모드: 모든 선택 상태 초기화
        old_district = st.session_state.selected_district
        old_quintile = st.session_state.selected_quintile

        st.session_state.selected_district = None
        st.session_state.selected_quintile = None
        clear_comparison_mode()

        log_state_change("clear_district_from_overview", old_district, None)
        log_state_change("clear_quintile_from_overview", old_quintile, None)

    elif stage == "gu_ranking":
        # 가격 5분위 모드: 자치구 선택 및 비교 상태 초기화
        old_district = st.session_state.selected_district

        st.session_state.selected_district = None
        clear_comparison_mode()

        log_state_change("clear_district_from_ranking", old_district, None)

    elif stage == "district_selected":
        # 자치구 선택 모드: 비교 상태만 초기화
        clear_comparison_mode()

    elif stage == "comparison":
        # 자치구 비교 모드: 자치구가 선택되어 있어야 함
        if not st.session_state.selected_district:
            # 자치구가 선택되지 않았으면 자치구 선택 모드로 변경
            logger.warning(
                "Comparison mode requires selected district, redirecting to district_selected"
            )
            st.session_state.view_stage = "district_selected"
            log_state_change(
                "redirect_to_district_selected", stage, "district_selected"
            )

    return True


def set_ranking_df(df: pd.DataFrame):
    """랭킹 데이터프레임을 저장합니다."""
    st.session_state.ranking_df = df


def clear_ranking_df():
    """랭킹 데이터프레임을 삭제합니다."""
    st.session_state.ranking_df = None


def select_district(district_name: str):
    """자치구를 선택합니다."""
    if not district_name or not isinstance(district_name, str):
        logger.error(f"Invalid district_name: {district_name}")
        return False

    old_district = st.session_state.get("selected_district")
    log_state_change("select_district", old_district, district_name)

    st.session_state.selected_district = district_name
    return True


def clear_selected_district():
    """선택된 자치구를 초기화합니다."""
    old_district = st.session_state.get("selected_district")
    log_state_change("clear_selected_district", old_district, None)

    st.session_state.selected_district = None


def select_quintile(quintile: int | None):
    """가격 구간을 선택합니다."""
    if quintile is not None and (
        not isinstance(quintile, int) or quintile < 1 or quintile > 5
    ):
        logger.error(f"Invalid quintile: {quintile}")
        return False

    old_quintile = st.session_state.get("selected_quintile")

    if st.session_state.selected_quintile == quintile:
        st.session_state.selected_quintile = None  # Toggle off
        log_state_change("toggle_off_quintile", old_quintile, None)
    else:
        st.session_state.selected_quintile = quintile
        log_state_change("select_quintile", old_quintile, quintile)

    return True


def add_message(role: str, content: str):
    """채팅 메시지를 추가합니다."""
    if not role or not content:
        logger.error(f"Invalid message parameters - role: {role}, content: {content}")
        return False

    if role not in ["user", "assistant"]:
        logger.warning(f"Unexpected role: {role}")

    try:
        st.session_state.messages.append({"role": role, "content": content})
        logger.debug(f"Added message - role: {role}, length: {len(content)}")
        return True
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        return False


# --- 비교 모드 관련 함수 ---


def set_comparison_mode(mode: str):
    """비교 모드를 설정합니다. ('adjacent' 또는 'similar_price')"""
    if not validate_comparison_mode(mode):
        logger.error(f"Invalid comparison_mode: {mode}")
        return False

    old_mode = st.session_state.get("comparison_mode")
    log_state_change("set_comparison_mode", old_mode, mode)

    st.session_state.comparison_mode = mode

    # 비교 모드 변경 시 기존 비교 대상 자치구 초기화
    if old_mode != mode:
        st.session_state.comparison_districts = []
        log_state_change(
            "clear_comparison_districts_on_mode_change", "previous_districts", []
        )

    return True


def clear_comparison_mode():
    """비교 모드를 초기화합니다."""
    old_mode = st.session_state.get("comparison_mode")
    old_districts = st.session_state.get("comparison_districts", [])

    log_state_change("clear_comparison_mode", old_mode, None)
    if old_districts:
        log_state_change(
            "clear_comparison_districts", f"{len(old_districts)} districts", []
        )

    st.session_state.comparison_mode = None
    st.session_state.comparison_districts = []


def set_comparison_districts(districts: list):
    """비교 대상 자치구 목록을 설정합니다."""
    if not isinstance(districts, list):
        logger.error(f"Invalid districts type: {type(districts)}")
        return False

    old_districts = st.session_state.get("comparison_districts", [])
    log_state_change(
        "set_comparison_districts",
        f"{len(old_districts)} districts",
        f"{len(districts)} districts",
    )

    st.session_state.comparison_districts = districts
    return True


# --- 세션 상태 진단 및 복구 함수 ---


def get_session_state_summary() -> dict:
    """현재 세션 상태의 요약 정보를 반환합니다."""
    return {
        "view_stage": st.session_state.get("view_stage"),
        "selected_district": st.session_state.get("selected_district"),
        "selected_quintile": st.session_state.get("selected_quintile"),
        "comparison_mode": st.session_state.get("comparison_mode"),
        "comparison_districts_count": len(
            st.session_state.get("comparison_districts", [])
        ),
        "messages_count": len(st.session_state.get("messages", [])),
        "is_valid": validate_session_state(),
    }


def repair_session_state():
    """손상된 세션 상태를 복구합니다."""
    logger.info("Starting session state repair")

    # 기본값으로 초기화
    if not validate_view_stage(st.session_state.get("view_stage")):
        logger.warning("Invalid view_stage detected, resetting to overview")
        st.session_state.view_stage = "overview"

    if not validate_comparison_mode(st.session_state.get("comparison_mode")):
        logger.warning("Invalid comparison_mode detected, resetting to None")
        st.session_state.comparison_mode = None
        st.session_state.comparison_districts = []

    # 비교 모드인데 자치구가 없는 경우
    if st.session_state.view_stage == "comparison" and not st.session_state.get(
        "selected_district"
    ):
        logger.warning(
            "Comparison mode without district, switching to district_selected"
        )
        st.session_state.view_stage = "district_selected"

    logger.info("Session state repair completed")


# --- 지도 캐시 관련 함수 (기존과 동일) ---
def get_map_from_cache(key: str = "map_html") -> str | None:
    """Streamlit 세션 상태에서 지도 HTML을 조회합니다."""
    return st.session_state.get(key)


def set_map_to_cache(map_html: str, key: str = "map_html"):
    """Streamlit 세션 상태에 지도 HTML을 저장합니다."""
    st.session_state[key] = map_html


def clear_map_cache(key: str):
    """Streamlit 세션 상태에서 특정 지도 캐시를 삭제합니다."""
    if key in st.session_state:
        del st.session_state[key]


def is_map_cached(key: str) -> bool:
    """지도 캐시 존재 여부를 확인합니다."""
    return key in st.session_state
