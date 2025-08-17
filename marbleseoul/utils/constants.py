#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""constants.py
Marble서울 프로젝트에서 사용하는 상수들을 정의합니다.
"""
from __future__ import annotations
import pathlib

# --- 경로 상수 ---
# 이 파일의 위치를 기준으로 프로젝트 루트 디렉토리를 찾습니다.
# (marble/marbleseoul/utils/constants.py -> marble/marbleseoul)
PACKAGE_DIR = pathlib.Path(__file__).resolve().parents[1]

SHP_FILE_PATH = PACKAGE_DIR / "resources" / "maps" / "서울행정동.shp"
APT_PRICE_STATS_PATH = (
    PACKAGE_DIR / "output" / "realprice" / "apt_trade_enriched_2024_stats.csv"
)
APT_COMPACT_PATH = (
    PACKAGE_DIR / "output" / "realprice" / "apt_trade_enriched_2024_compact.csv"
)
DONG_STATS_PATH = (
    PACKAGE_DIR / "output" / "dong_stats_2024" / "dong_stats_merged_2024.csv"
)
NATIONAL_RANKING_PATH = PACKAGE_DIR / "output" / "rankings" / "전국퍼센트랭킹.csv"
SEOUL_RANKING_PATH = PACKAGE_DIR / "output" / "rankings" / "서울퍼센트랭킹.csv"


# --- 지도 관련 상수 ---
SEOUL_CENTER_COORD = [37.5665, 126.9780]  # 서울 중심 좌표
SEOUL_GU_MAPPING = {
    "11010": "종로구",
    "11020": "중구",
    "11030": "용산구",
    "11040": "성동구",
    "11050": "광진구",
    "11060": "동대문구",
    "11070": "중랑구",
    "11080": "성북구",
    "11090": "강북구",
    "11100": "도봉구",
    "11110": "노원구",
    "11120": "은평구",
    "11130": "서대문구",
    "11140": "마포구",
    "11150": "양천구",
    "11160": "강서구",
    "11170": "구로구",
    "11180": "금천구",
    "11190": "영등포구",
    "11200": "동작구",
    "11210": "관악구",
    "11220": "서초구",
    "11230": "강남구",
    "11240": "송파구",
    "11250": "강동구",
}

# 자치구별 중심점 좌표 (자치구 줌인 기능용)
SEOUL_GU_CENTER_COORDS = {
    "종로구": [37.5735, 126.9792],  # 종로구청 인근
    "중구": [37.5641, 126.9976],  # 중구청 인근
    "용산구": [37.5326, 126.9895],  # 용산구청 인근
    "성동구": [37.5633, 127.0369],  # 성동구청 인근
    "광진구": [37.5384, 127.0822],  # 광진구청 인근
    "동대문구": [37.5744, 127.0398],  # 동대문구청 인근
    "중랑구": [37.6066, 127.0925],  # 중랑구청 인근
    "성북구": [37.5894, 127.0166],  # 성북구청 인근
    "강북구": [37.6397, 127.0256],  # 강북구청 인근
    "도봉구": [37.6668, 127.0471],  # 도봉구청 인근
    "노원구": [37.6543, 127.0565],  # 노원구청 인근
    "은평구": [37.6026, 126.9289],  # 은평구청 인근
    "서대문구": [37.5791, 126.9368],  # 서대문구청 인근
    "마포구": [37.5663, 126.9019],  # 마포구청 인근
    "양천구": [37.5169, 126.8664],  # 양천구청 인근
    "강서구": [37.5509, 126.8495],  # 강서구청 인근
    "구로구": [37.4954, 126.8874],  # 구로구청 인근
    "금천구": [37.4569, 126.8954],  # 금천구청 인근
    "영등포구": [37.5263, 126.8962],  # 영등포구청 인근
    "동작구": [37.5124, 126.9392],  # 동작구청 인근
    "관악구": [37.4784, 126.9516],  # 관악구청 인근
    "서초구": [37.4837, 127.0323],  # 서초구청 인근
    "강남구": [37.5172, 127.0473],  # 강남구청 인근
    "송파구": [37.5145, 127.1059],  # 송파구청 인근
    "강동구": [37.5301, 127.1238],  # 강동구청 인근
}
QUINTILE_COLORS = ["#d73027", "#fc8d59", "#fee090", "#91bfdb", "#4575b4"]  # ColorBrewer

# --- 챗봇 관련 상수 ---
RANKING_KEYWORDS = ["랭킹", "네", "보여", "순위"]
RESET_KEYWORDS = ["전체", "초기", "처음", "돌아가"]

# --- 캐시 키 상수 ---
MAP_HTML_SEOUL_TOTAL = "__MAP_HTML_SEOUL_TOTAL_V3__"
MAP_HTML_GU_RANKING_PREFIX = "__MAP_HTML_GU_RANKING_Q"
MAP_HTML_DISTRICT_ZOOM_PREFIX = "__MAP_HTML_DISTRICT_ZOOM_"
