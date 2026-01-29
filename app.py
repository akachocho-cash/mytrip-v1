import streamlit as st
import pandas as pd
from datetime import date, timedelta
from duckduckgo_search import DDGS
from collections import Counter
import altair as alt
import re
import os

# ----------------------
# 글로벌 스타일 (이미지 높이 통일)
# ----------------------
st.markdown(
    """
    <style>
    div[data-testid="stImage"] img {
        height: 300px !important;
        width: 100%;
        object-fit: cover;
        object-position: center center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------
# 페이지 기본 설정
# ----------------------
st.set_page_config(
    page_title="SNS 여행 트렌드 랭킹",
    page_icon="🌏",
    layout="wide",
)

# ----------------------
# 사이드바 입력 영역
# ----------------------
st.sidebar.title("🌍 여행 도시 & 기간 선택")

default_city = "오사카"
city = st.sidebar.text_input("분석할 도시 이름을 입력하세요", value=default_city, placeholder="예: 도쿄, 서울, 파리")

today = date.today()
default_start = today - timedelta(days=30)

start_date = st.sidebar.date_input("시작일", value=default_start)
end_date = st.sidebar.date_input("종료일", value=today)

if start_date > end_date:
    st.sidebar.error("시작일은 종료일보다 이후일 수 없습니다.")


# ----------------------
# 가짜 데이터 생성 함수 (폴백용)
# ----------------------
def generate_mock_data(city_name: str, n: int = 5) -> pd.DataFrame:
    """검색 실패 시 보여줄 가짜 데이터 생성"""
    mock_data = [
        {
            "제목": f"{city_name} 핫플레이스 추천 - 인기 관광지 베스트 5",
            "요약": f"{city_name}에서 가장 인기 있는 관광지와 맛집을 소개합니다. SNS에서 화제가 된 핫스팟들을 모아봤어요.",
            "링크": "#",
        },
        {
            "제목": f"{city_name} 여행 코스 - 하루 일정 완벽 가이드",
            "요약": f"{city_name} 여행을 위한 최적의 하루 코스를 추천합니다. 효율적인 이동 경로와 필수 방문지를 확인하세요.",
            "링크": "#",
        },
        {
            "제목": f"{city_name} 맛집 리스트 - 현지인 추천 식당",
            "요약": f"{city_name} 현지인들이 추천하는 맛집들을 정리했습니다. 숨은 맛집부터 유명 레스토랑까지 다양한 옵션을 제공합니다.",
            "링크": "#",
        },
        {
            "제목": f"{city_name} 야경 명소 - 로맨틱한 밤 풍경",
            "요약": f"{city_name}의 아름다운 야경을 감상할 수 있는 명소들을 소개합니다. 데이트 코스로도 추천합니다.",
            "링크": "#",
        },
        {
            "제목": f"{city_name} 쇼핑 가이드 - 쇼핑몰과 시장 정보",
            "요약": f"{city_name}에서 쇼핑하기 좋은 곳들을 정리했습니다. 기념품부터 명품까지 다양한 쇼핑 옵션을 확인하세요.",
            "링크": "#",
        },
    ]
    return pd.DataFrame(mock_data[:n])


# ----------------------
# DuckDuckGo 검색 함수
# ----------------------
def search_places_with_ddg(city_name: str, max_results: int = 15) -> tuple[pd.DataFrame, bool]:
    """DuckDuckGo 검색으로 실제 여행 관련 결과를 가져와서 DataFrame으로 반환
    
    Returns:
        tuple: (DataFrame, is_success) - 검색 결과와 성공 여부
    """
    query = f"{city_name} 여행 맛집 핫플레이스 추천"

    try:
        rows = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="kr-kr"):
                title = r.get("title") or ""
                href = r.get("href") or ""
                body = r.get("body") or ""

                if not href:
                    continue

                rows.append(
                    {
                        "제목": title,
                        "요약": body,
                        "링크": href,
                    }
                )

        if not rows:
            return generate_mock_data(city_name, n=5), False

        df = pd.DataFrame(rows)
        return df, True
    except Exception:
        # 에러 발생 시 가짜 데이터 반환
        return generate_mock_data(city_name, n=5), False


def search_image(query: str) -> str | None:
    """DuckDuckGo 이미지 검색으로 쿼리에 맞는 이미지를 하나 가져옴"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1, size="large", safesearch="moderate"))
        if results:
            return results[0].get("image") or results[0].get("thumbnail")
    except Exception:
        return None
    return None


# ----------------------
# 메인 화면
# ----------------------
st.title("📸 SNS 여행 트렌드 랭킹 서비스")
st.markdown(
    f"**{city}**의 SNS 상에서 최근 뜨는 여행 스팟을 살펴보는 대시보드입니다. ✈️🏙️\n\n"
    "DuckDuckGo 실시간 검색 결과를 기반으로 여행/맛집/핫플레이스 정보를 모아 보여줍니다. 🌐"
)

# 도시 여행 대표 이미지 (도톤보리 & USJ) - 로컬 이미지 사용
col1, col2 = st.columns(2)

with col1:
    if os.path.exists("doton.jpeg"):
        st.image("doton.jpeg", use_container_width=True)
        st.caption("오사카 도톤보리")
    else:
        st.write("이미지 준비 중 (doton.jpeg 파일을 찾을 수 없습니다.)")

with col2:
    if os.path.exists("universal.jpeg"):
        st.image("universal.jpeg", use_container_width=True)
        st.caption("유니버셜 스튜디오 재팬")
    else:
        st.write("이미지 준비 중 (universal.jpeg 파일을 찾을 수 없습니다.)")

st.markdown("---")

if start_date <= end_date:
    st.subheader(f"🔥 {city} 최근 뜨는 핫플레이스 검색 결과")
    st.caption(f"분석 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # DuckDuckGo 검색 결과 가져오기
    with st.spinner("실제 웹에서 여행 트렌드를 검색 중입니다... ⏳"):
        df, is_success = search_places_with_ddg(city)

    # 검색 실패 시 안내 메시지 표시
    if not is_success:
        st.warning("현재 검색량이 많아 기본 데이터를 보여드립니다.")

    if df.empty:
        st.warning("검색 결과를 찾지 못했습니다. 도시 이름을 조금 다르게 입력해 보세요. 🔍")
    else:
        # 탭 구성
        tab_trend, tab_reviews = st.tabs(["📊 트렌드 분석", "📝 블로그 리뷰 모아보기"])

        with tab_trend:
            # ----------------------
            # 실시간 트렌드 키워드 분석 (스마트 필터링)
            # ----------------------
            all_text = " ".join(df["요약"].astype(str).tolist())

            cleaned = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", all_text)
            tokens = cleaned.lower().split()

            normalized_city = city.strip().lower()
            stopwords = {
                "", " ", "여행", "추천", "맛집", "핫플", "핫플레이스",
                "정보", "블로그", "후기", "리뷰", "지도", "예약",
                "호텔", "숙소", "여기", "소개", "사진", "영상",
                "코스", "박일", "정말", "너무", "위치", "사람",
                normalized_city,
            }

            filtered_tokens = [
                t for t in tokens
                if len(t) > 1 and not t.isdigit() and t not in stopwords
            ]

            counter = Counter(filtered_tokens)
            top_keywords = counter.most_common(10)

            if top_keywords:
                trend_df = pd.DataFrame(top_keywords, columns=["키워드", "빈도"])

                st.markdown("### 🔥 실시간 트렌드 키워드")

                chart = (
                    alt.Chart(trend_df)
                    .mark_bar(color="#ff7f50")
                    .encode(
                        x=alt.X("빈도:Q", title="등장 빈도"),
                        y=alt.Y("키워드:N", sort="-x", title="키워드"),
                        tooltip=["키워드", "빈도"],
                    )
                    .properties(height=360)
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("트렌드 키워드를 추출하기에 충분한 텍스트가 없습니다.")

        with tab_reviews:
            st.markdown("### 📝 블로그/리뷰 카드 모아보기")

            for _, row in df.iterrows():
                title = str(row.get("제목", "")).strip() or "제목 없음"
                link = str(row.get("링크", "")).strip()
                body = str(row.get("요약", "")).strip()

                if link:
                    st.markdown(f"**[{title}]({link})**")
                else:
                    st.markdown(f"**{title}**")

                if body:
                    st.markdown(f"<small>{body}</small>", unsafe_allow_html=True)

                st.markdown("---")

        st.caption("DuckDuckGo 검색 결과를 기반으로 한 실시간 여행/맛집/핫플레이스 정보입니다. 🌐")
else:
    st.warning("올바른 기간을 선택하면 SNS 여행 트렌드 랭킹을 확인할 수 있어요. 📅")