# marble/marbleseoul/maps/base_map.py
import folium

from ..utils import constants as const


def create_base_map(location=const.SEOUL_CENTER_COORD, zoom_start=11):
    """
    Folium 기본 지도를 생성합니다.

    Args:
        location (tuple, optional): 지도 중심 좌표. Defaults to const.SEOUL_CENTER_COORD.
        zoom_start (int, optional): 초기 줌 레벨. Defaults to 11.

    Returns:
        folium.Map: Folium 지도 객체.
    """
    return folium.Map(location=location, zoom_start=zoom_start, tiles="cartodbpositron")
