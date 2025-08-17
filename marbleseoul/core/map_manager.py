#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""map_manager.py
Marble서울 지도 생성, 캐싱, 렌더링 관리
"""
from __future__ import annotations

import streamlit as st

from marbleseoul.core import cache_manager
from marbleseoul.maps import base_map, seoul_total, gu_ranking
from marbleseoul.utils import constants as const


def display_map(
    state, latest_month, latest_avg_price, gugun_ranking_df, price_quintiles
):
    """
    현재 상태에 맞는 지도를 생성, 캐싱하고 Streamlit에 표시합니다.
    액션이 필요한 경우 액션 정보를 반환합니다.
    """
    current_view = state.view_stage
    map_action = None

    # 1. 서울 전체 지도 캐싱
    if not cache_manager.is_map_cached(const.MAP_HTML_SEOUL_TOTAL):
        seoul_map = base_map.create_base_map(
            location=const.SEOUL_CENTER_COORD, zoom_start=11
        )
        map_html = seoul_total.create_seoul_total_map(
            seoul_map, latest_month, latest_avg_price
        )
        cache_manager.set_map_to_cache(map_html, const.MAP_HTML_SEOUL_TOTAL)

    # 2. 자치구 랭킹 지도 캐싱 (필요시)
    # 인접 자치구 정보가 있으면 캐시 키에 포함
    adjacent_districts = getattr(state, "comparison_districts", None)
    # 비어있는 리스트도 None으로 처리
    if adjacent_districts and len(adjacent_districts) > 0:
        adjacent_cache_suffix = f"_adj_{'_'.join(sorted(adjacent_districts))}"
    else:
        adjacent_cache_suffix = ""
        adjacent_districts = None  # 빈 리스트를 None으로 변경

    map_cache_key = f"{const.MAP_HTML_GU_RANKING_PREFIX}{state.selected_quintile}__{adjacent_cache_suffix}"

    # 지도 캐시 확인 및 생성

    if not cache_manager.is_map_cached(map_cache_key):
        gu_map = base_map.create_base_map(
            location=const.SEOUL_CENTER_COORD, zoom_start=11
        )
        map_html = gu_ranking.create_gu_ranking_map(
            gu_map,
            gugun_ranking_df,
            price_quintiles,
            state.selected_quintile,
            state.selected_district,
            adjacent_districts,
            state.comparison_mode,
        )
        cache_manager.set_map_to_cache(map_html, map_cache_key)

    # 3. 자치구 줌인 지도 캐싱 (선택된 자치구가 있을 때)
    if state.selected_district:
        district_cache_key = f"{const.MAP_HTML_DISTRICT_ZOOM_PREFIX}{state.selected_district}__{adjacent_cache_suffix}"
        if not cache_manager.is_map_cached(district_cache_key):
            # 선택된 자치구의 중심점 좌표 가져오기
            district_center = const.SEOUL_GU_CENTER_COORDS.get(
                state.selected_district, const.SEOUL_CENTER_COORD
            )
            # 자치구 줌인 지도 생성 (zoom_start=13으로 더 확대)
            district_map = base_map.create_base_map(
                location=district_center, zoom_start=13
            )
            # 선택된 자치구와 인접 자치구 하이라이트하여 표시
            map_html = gu_ranking.create_district_zoom_map(
                district_map,
                gugun_ranking_df,
                state.selected_district,
                adjacent_districts,
                state.comparison_mode,
            )
            cache_manager.set_map_to_cache(map_html, district_cache_key)

    # 4. 현재 상태에 따라 지도 렌더링
    try:
        if state.selected_district:  # 자치구가 선택된 경우: 줌인 지도 표시
            district_cache_key = f"{const.MAP_HTML_DISTRICT_ZOOM_PREFIX}{state.selected_district}__{adjacent_cache_suffix}"
            map_html = cache_manager.get_map_from_cache(district_cache_key)
            if map_html:
                st.components.v1.html(map_html, width=700, height=600)
                st.caption(f"🎯 **{state.selected_district}** 상세 분석 모드")
            else:
                st.warning(
                    f"⚠️ {state.selected_district} 지도를 생성 중입니다. 잠시만 기다려주세요..."
                )
                map_action = {
                    "type": "refresh_map",
                    "reason": "district_zoom_cache_missing",
                }
        elif current_view == "gu_ranking":  # 자치구별 랭킹 모드
            # 🎯 구간 선택 UI 추가
            st.markdown("#### 📊 가격 구간 선택")
            st.info("구간을 선택하면 해당 자치구들이 지도에서 강조 표시됩니다.")
            
            # 5개 구간 버튼을 한 줄에 배치
            cols = st.columns(5)
            
            for i, col in enumerate(cols, 1):
                with col:
                    quintile_data = price_quintiles[i]
                    button_style = "primary" if state.selected_quintile == i else "secondary"
                    
                    if st.button(
                        f"{quintile_data['label']}\n{quintile_data['description']}",
                        key=f"quintile_{i}",
                        use_container_width=True,
                        type=button_style,
                        help=f"가격 범위: {quintile_data['price_range']}"
                    ):
                        # 같은 구간 클릭시 토글 (선택 해제)
                        if state.selected_quintile == i:
                            map_action = ("quintile_selected", None)
                        else:
                            map_action = ("quintile_selected", i)
            
            # 구간 해제 버튼
            if state.selected_quintile:
                if st.button("🔄 전체 구간 보기", use_container_width=True):
                    map_action = ("quintile_selected", None)
            
            st.markdown("---")
            
            # 지도 표시
            map_cache_key = (
                f"{const.MAP_HTML_GU_RANKING_PREFIX}{state.selected_quintile}__"
            )
            map_html = cache_manager.get_map_from_cache(map_cache_key)
            if map_html:
                st.components.v1.html(map_html, width=700, height=600)
                
                # 선택된 구간 정보 표시
                if state.selected_quintile:
                    quintile_info = price_quintiles[state.selected_quintile]
                    st.success(f"🎯 **{quintile_info['label']}** 선택됨 - {quintile_info['description']} ({quintile_info['count']}개 자치구)")
                else:
                    st.caption("🔍 자치구별 가격 5분위 전체 모드")
            else:
                st.warning("⚠️ 자치구별 지도를 생성 중입니다. 잠시만 기다려주세요...")
                map_action = {
                    "type": "refresh_map",
                    "reason": "gu_ranking_cache_missing",
                }
        else:  # "overview" 또는 기타: 서울 전체 현황
            map_html = cache_manager.get_map_from_cache(const.MAP_HTML_SEOUL_TOTAL)
            if map_html:
                st.components.v1.html(map_html, width=700, height=600)
                st.caption("🏙️ 서울 전체 현황 모드")
            else:
                st.warning("⚠️ 서울 전체 지도를 생성 중입니다. 잠시만 기다려주세요...")
                map_action = {
                    "type": "refresh_map",
                    "reason": "seoul_total_cache_missing",
                }
    except Exception as e:
        st.error(f"❌ 지도 표시 중 오류가 발생했습니다: {str(e)}")
        if st.button("🔄 지도 다시 생성", key="regenerate_map"):
            if state.selected_district:  # 자치구 줌인 지도 캐시 삭제
                district_cache_key = (
                    f"{const.MAP_HTML_DISTRICT_ZOOM_PREFIX}{state.selected_district}__"
                )
                cache_manager.clear_map_cache(district_cache_key)
            elif current_view == "gu_ranking":  # 자치구 랭킹 지도 캐시 삭제
                map_cache_key = (
                    f"{const.MAP_HTML_GU_RANKING_PREFIX}{state.selected_quintile}__"
                )
                cache_manager.clear_map_cache(map_cache_key)
            else:  # 서울 전체 지도 캐시 삭제
                cache_manager.clear_map_cache(const.MAP_HTML_SEOUL_TOTAL)
            map_action = {"type": "refresh_map", "reason": "user_requested_regenerate"}

    return map_action
