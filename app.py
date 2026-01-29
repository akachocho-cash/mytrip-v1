import streamlit as st
import pandas as pd
from datetime import date, timedelta
from duckduckgo_search import DDGS
from collections import Counter
import altair as alt
import re
import os
import google.generativeai as genai
import time

# ----------------------
# 1. 페이지 기본 설정 및 스타일
# ----------------------
st.set_page_config(
    page_title="SNS 여행 트렌드 랭킹",
    page_icon="🌏",
    layout="wide",
)

# 이미지 높이 강제 통일 (CSS)
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
# 2. 기능 함수들 (AI, 검색, 데이터)
# ----------------------

def setup_gemini():
    """Gemini API 키 설정 및 모델 준비"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return None

def analyze_with_gemini(city_name: str, content_text: str):
    """Gemini AI(Flash Latest)로 여행 도시 분석 - 텍스트 추출 버전"""
    try:
        # ✅ 성공한 모델: gemini-flash-latest
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = f"""
        다음은 '{city_name}'에 대한 최신 여행 검색 정보입니다:
        {content_text}
        
        위 정보를 바탕으로 다음을 수행해줘:
        1. 이 도시가 지금 인기 있는 이유를 3줄로 요약.
        2. 여행객 성향(커플, 가족, 혼자 등)에 따른 추천 멘트 한 줄.
        3. 말투는 친절한 여행 가이드처럼 해줘.
        """
        
        # 스트리밍 요청
        response = model.generate_content(prompt, stream=True)
        
        # 🚨 여기가 핵심 수정! 
        # 상자(Response)를 뜯어서 내용물(Text)만 한 조각씩 화면에 던져줍니다.
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        # 에러가 나면 여기서 잡힙니다.
        # st.error(f"AI 호출 중 오류: {e}") # 필요하면 주석 해제
        yield f"죄송합니다. AI 분석 중 오류가 발생했습니다. ({e})"

def generate_mock_data(city_name: str, n: int = 5) -> pd.DataFrame:
    """검색 실패 시 보여줄 가짜 데이터"""
    mock_data = [
        {"제목": f"{city_name} 3박 4일 완벽 코스", "요약": "현지인이 추천하는 알짜배기 코스 모음입니다.", "링크": "#"},
        {"제목": f"{city_name} 맛집 BEST 5", "요약": "줄 서서 먹는다는 그곳, 솔직 후기!", "링크": "#"},
        {"제목": f"{city_name} 숙소 추천", "요약": "가성비와 위치 모두 잡은 호텔 리스트.", "링크": "#"},
        {"제목": f"실시간 {city_name} 날씨와 옷차림", "요약": "지금 여행하기 딱 좋은 날씨네요.", "링크": "#"},
        {"제목": f"{city_name} 쇼핑 리스트", "요약": "이건 꼭 사야 해! 필수 기념품 정리.", "링크": "#"},
    ]
    return pd.DataFrame(mock_data[:n])

def search_places_with_ddg(city_name: str, max_results: int = 10) -> tuple[pd.DataFrame, bool]:
    """DuckDuckGo 검색 (실패 시 Mock Data 반환)"""
    query = f"{city_name} 여행 추천 코스 맛집"
    try:
        rows = []
        # 검색 시도
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="kr-kr"):
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")
                if href:
                    rows.append({"제목": title, "요약": body, "링크": href})
        
        if not rows:
            return generate_mock_data(city_name), False
            
        return pd.DataFrame(rows), True
        
    except Exception as e:
        # 검색 에러 발생 시
        # print(f"검색 에러: {e}") # 디버깅용
        return generate_mock_data(city_name), False

# ----------------------
# 3. 사이드바 (입력 창)
# ----------------------
st.sidebar.title("🌍 여행 도시 선택")
city = st.sidebar.text_input("도시 이름", value="오사카", placeholder="예: 도쿄, 서울, 파리")
st.sidebar.caption("📅 기간: 최근 30일 트렌드 분석")

# ----------------------
# 4. 메인 화면 구성
# ----------------------
st.title(f"✈️ {city} 여행 트렌드 분석")

# 이미지 섹션 (로컬 파일 체크)
col1, col2 = st.columns(2)

# ※ 파일명이 정확해야 합니다! (doton.jpeg / universal.jpeg)
img1_path = "doton.jpeg" 
img2_path = "universal.jpeg"

with col1:
    if os.path.exists(img1_path):
        st.image(img1_path, use_container_width=True, caption="도시의 랜드마크")
    else:
        st.info(f"'{img1_path}' 이미지가 폴더에 없습니다.")

with col2:
    if os.path.exists(img2_path):
        st.image(img2_path, use_container_width=True, caption="주요 관광지")
    else:
        st.info(f"'{img2_path}' 이미지가 폴더에 없습니다.")

st.divider()

# ----------------------
# 5. 데이터 분석 및 AI 리포트
# ----------------------
if st.button("🚀 트렌드 분석 시작하기", type="primary"):
    
    with st.spinner(f"🔍 '{city}'에 대한 최신 정보를 긁어모으고 있습니다..."):
        df, is_success = search_places_with_ddg(city)
    
    if not is_success:
        st.warning("⚠️ 실시간 검색량이 많아 '기본 데이터'로 분석합니다.")
    else:
        st.success(f"✅ 최신 정보 {len(df)}건을 찾았습니다!")

    # 탭 생성
    tab_ai, tab_list = st.tabs(["🤖 AI 여행 분석가", "📝 검색 결과 리스트"])

    # [탭 1] AI 분석
    with tab_ai:
        st.subheader(f"🤖 Gemini가 분석한 {city} 여행 포인트")
        
        if setup_gemini():
            # 검색된 텍스트 합치기
            combined_text = " ".join(df["요약"].astype(str).tolist())
            
            st.write("✍️ AI가 보고서를 작성 중입니다...")
            
            # 분석 함수 호출
            response_stream = analyze_with_gemini(city, combined_text)
            
            if response_stream:
                st.write_stream(response_stream)
            else:
                st.error("AI 응답을 받아오지 못했습니다.")
        else:
            st.error("⚠️ secrets.toml 파일에 API 키가 없거나 잘못되었습니다.")

    # [탭 2] 리스트 보기
    with tab_list:
        st.subheader("🔗 관련 블로그 & 정보")
        for idx, row in df.iterrows():
            st.markdown(f"**{idx+1}. [{row['제목']}]({row['링크']})**")
            st.caption(row['요약'])
            st.markdown("---")

else:
    st.info("왼쪽 사이드바에서 도시를 확인하고 '분석 시작하기' 버튼을 눌러주세요! 👆")