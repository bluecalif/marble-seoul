import pandas as pd


def get_dong_apartment_info(apt_price_df, district_name, dong_name):
    """선택된 자치구 및 행정동의 아파트 정보를 분석합니다."""
    # 자치구와 행정동으로 데이터 필터링
    dong_df = apt_price_df[
        (apt_price_df["gugun"] == district_name) & (apt_price_df["dong"] == dong_name)
    ]

    if dong_df.empty:
        return None

    # 기본 통계 정보 계산
    total_complexes = dong_df["apt_name"].nunique()
    avg_price = dong_df["price_84m2_manwon"].mean()
    min_price_row = dong_df.loc[dong_df["price_84m2_manwon"].idxmin()]
    max_price_row = dong_df.loc[dong_df["price_84m2_manwon"].idxmax()]
    avg_build_year = dong_df["build_year"].mean()
    # district_analyzer와 동일한 세대수 계산 방식 (중복 제거)
    total_households = dong_df.groupby("apt_name")["household_count"].first().sum()

    # 상위 5개 아파트 선정
    top_5_apartments = (
        dong_df.groupby("apt_name")["price_84m2_manwon"]
        .mean()
        .nlargest(5)
        .reset_index()
    )
    top_5_apartments.columns = ["아파트명", "평균 가격(만원)"]
    top_5_apartments["평균 가격(만원)"] = top_5_apartments["평균 가격(만원)"].apply(
        lambda x: f"{x:,.0f}"
    )

    summary = {
        "총 단지 수": total_complexes,
        "평균 가격(만원)": f"{avg_price:,.0f}",
        "최고가": f"{max_price_row['price_84m2_manwon']:,.0f} ({max_price_row['apt_name']})",
        "최저가": f"{min_price_row['price_84m2_manwon']:,.0f} ({min_price_row['apt_name']})",
        "평균 건축년도": f"{avg_build_year:.0f}년",
        "총 세대수": f"{total_households:,.0f}",
    }

    return {"summary": summary, "top_5": top_5_apartments}
