import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import base64
import os
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="이투스247학원 입시 검색기", layout="wide")

# =========================== #
# 1. 대학 정보 CSV 불러오기
# =========================== #
univ_info_df = pd.read_csv("univ_info.csv")  # 대학 정보 CSV 경로
univ_info_dict = univ_info_df.set_index("대학교명")[["url", "desc"]].to_dict(orient="index")

# =========================== #
# 2. 이미지(SVG/PNG) 불러오기
# =========================== #
def image_to_base64_with_type(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".svg":
            mime = "image/svg+xml"
        elif ext == ".jpg" or ext == ".jpeg":
            mime = "image/jpeg"
        else:
            mime = "image/png"
        return encoded, mime
    except Exception:
        return None, None

def get_logo_base64_with_type(univ_name, dark_mode=False):
    mode_folder = 'dark' if dark_mode else 'light'
    fallback_folder = 'light' if dark_mode else 'dark'

    for ext in [".svg", ".png"]:
        img_path = f"./univ_logos/{mode_folder}/{univ_name}{ext}"
        encoded, mime = image_to_base64_with_type(img_path)
        if encoded:
            return encoded, mime

    for ext in [".svg", ".png"]:
        img_path = f"./univ_logos/{fallback_folder}/{univ_name}{ext}"
        encoded, mime = image_to_base64_with_type(img_path)
        if encoded:
            return encoded, mime

    return None, None

# =========================== #
# 3. 데이터 로딩
# =========================== #
@st.cache_data
def load_data():
    df = pd.read_excel("2026 3개년 입결.xlsx", sheet_name="전체")
    df.columns = df.columns.str.replace("\n", "").str.strip()
    if '2025학년도경쟁률' in df.columns:
        df.rename(columns={'2025학년도경쟁률': '2025경쟁률'}, inplace=True)
    return df

df = load_data()

# =========================== #
# 4. 실 브라우저 다크모드 감지
# =========================== #
is_dark = streamlit_js_eval(
    js_expressions='window.matchMedia("(prefers-color-scheme: dark)").matches',
    key="dark-mode"
)
dark_mode = bool(is_dark)

# ------------------------
# 로고 base64 변환
# ------------------------
def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = image_to_base64("이투스247학원 BI(기본형).png")

# ------------------------
# 로고 + 타이틀 출력
# ------------------------
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_base64}" alt="logo" style="height: 40px;">
    <h1 style="margin: 0; font-size: 40px;">입시 검색기</h1>
</div>
""", unsafe_allow_html=True)

st.caption("각 대학 모집단위별 3개년 수시 전형 결과를 한눈에 비교해보세요.")

# =========================== #
# 5. 대시보드 레이아웃
# =========================== #

cols = st.columns([5, 0.15, 5, 0.15, 5])
years = ['2023', '2024', '2025']
모집정보_컬럼 = [
    "모집인원", "모집인원(전년대비)", "전형방법", "복수지원", "최저학력기준",
    "전년대비 변경사항", "대학별고사 실시일"
]

for i, idx in enumerate([0, 2, 4], start=1):
    with cols[idx]:
        # 1. 대학 로고+링크+툴팁+아이콘
        default_univ = sorted(df['대학교'].unique())[0]
        univ_key = f"대학교_{i}"
        curr_univ = st.session_state.get(univ_key, default_univ)
        img_base64, img_mime = get_logo_base64_with_type(curr_univ, dark_mode)

        # 대학 정보 dict에서 자동 매칭
        univ_info = univ_info_dict.get(curr_univ, {})
        univ_url = univ_info.get("url", "#")
        univ_desc = univ_info.get("desc", curr_univ)

        if img_base64:
            st.markdown(
                f"""
                <style>
                .univ-logo-box-{i} {{
                    width: 320px;
                    height: 160px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: rgba(255,255,255,0.01);
                    margin: 18px auto 26px auto;
                    border-radius: 32px;
                    border: 1px solid #44444430;
                    position: relative;
                    box-sizing: border-box;
                    transition: box-shadow 0.2s;
                    padding-top: 8px; padding-bottom: 0;
                }}
                .univ-logo-box-{i}:hover {{
                    box-shadow: 0 4px 16px 0 #2d6cdf22;
                    background-color: rgba(255,255,255,0.08);
                }}
                .univ-logo-img-{i} {{
                    max-width: 220px;
                    max-height: 140px;
                    object-fit: contain;
                    display: block;
                    margin: 0 auto;
                    transition: transform 0.18s cubic-bezier(.4,2,.7,1), filter 0.2s;
                }}
                .univ-logo-box-{i}:hover .univ-logo-img-{i} {{
                    filter: brightness(1.12);
                    transform: scale(1.04);
                }}
                </style>
                <div class='univ-logo-box-{i}'>
                    <a href="{univ_url}" target="_blank" style="display:block; width:100%; height:100%;">
                        <img src='data:{img_mime};base64,{img_base64}'
                            title="{univ_desc} (클릭시 홈페이지 이동)"
                            class="univ-logo-img-{i}">
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )


        # 2. 대학교/계열/전형유형/전형명/모집단위 필터
        대학교 = st.selectbox("대학교", sorted(df['대학교'].unique()), key=univ_key)
        계열리스트 = sorted(df[df['대학교'] == 대학교]['계열'].dropna().unique())
        계열 = st.selectbox("계열", 계열리스트, key=f"계열_{i}")

        col_type, col_name = st.columns(2)
        with col_type:
            전형유형리스트 = sorted(df[(df['대학교'] == 대학교) & (df['계열'] == 계열)]['전형유형'].dropna().unique())
            전형유형 = st.selectbox("전형유형", 전형유형리스트, key=f"전형유형_{i}") if 전형유형리스트 else None
        with col_name:
            if 전형유형:
                전형명리스트 = sorted(df[
                    (df['대학교'] == 대학교) & (df['계열'] == 계열) & (df['전형유형'] == 전형유형)
                ]['전형명'].unique())
            else:
                전형명리스트 = []
            전형명 = st.selectbox("전형명", 전형명리스트, key=f"전형명_{i}") if 전형명리스트 else None

        if 전형유형 and 전형명:
            모집단위리스트 = sorted(df[
                (df['대학교'] == 대학교) &
                (df['계열'] == 계열) &
                (df['전형유형'] == 전형유형) &
                (df['전형명'] == 전형명)
            ]['모집단위명'].unique())
        else:
            모집단위리스트 = []
        모집단위 = st.selectbox("모집단위명", 모집단위리스트, key=f"모집단위명_{i}") if 모집단위리스트 else None

        # 3. 데이터 추출 및 시각화
        if 전형유형 and 전형명 and 모집단위:
            row = df[
                (df['대학교'] == 대학교) &
                (df['계열'] == 계열) &
                (df['전형유형'] == 전형유형) &
                (df['전형명'] == 전형명) &
                (df['모집단위명'] == 모집단위)
            ].head(1)
        else:
            row = pd.DataFrame()

        if row.empty:
            st.warning("선택하신 조합의 데이터가 없습니다.")
        else:
            st.markdown(f"**{대학교} {모집단위} [{전형유형}/{전형명}]**")
            입결 = [pd.to_numeric(row.iloc[0].get(f"{y}입결", None), errors='coerce') for y in years]
            경쟁률 = [pd.to_numeric(row.iloc[0].get(f"{y}경쟁률", None), errors='coerce') for y in years]
            충원 = [pd.to_numeric(row.iloc[0].get(f"{y}충원", None), errors='coerce') for y in years]

            입결기준라벨 = row.iloc[0].get("입결 기준", None)
            if pd.notnull(입결기준라벨) and str(입결기준라벨).strip() != "":
                yaxis_title = f"입결(등급, {입결기준라벨})"
            else:
                yaxis_title = "입결(등급, 낮을수록 우수)"

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=입결, mode='lines+markers',
                name='입결(등급)', yaxis='y1', line=dict(color='royalblue', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=years, y=경쟁률, mode='lines+markers',
                name='경쟁률', yaxis='y2', line=dict(color='orange', width=3, dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=years, y=충원, mode='lines+markers',
                name='충원인원', yaxis='y2', line=dict(color='green', width=3, dash='dot')
            ))
            fig.update_layout(
                xaxis=dict(title='연도', tickmode='linear'),
                yaxis=dict(title=yaxis_title, autorange='reversed', showgrid=False, side='left'),
                yaxis2=dict(title='경쟁률 / 충원인원', overlaying='y', side='right', showgrid=False),
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5, font=dict(size=11)),
                height=330,
                margin=dict(l=20, r=20, t=20, b=20)
            )

            # ✅ key 추가
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_chart_{i}")
            st.markdown("---")

            st.markdown('<div style="width:310px;"><b>2026학년도 모집 주요 정보</b></div>', unsafe_allow_html=True)
            df_display = pd.DataFrame([
                {"항목": colnm, "내용": row.iloc[0][colnm]}
                for colnm in 모집정보_컬럼
                if colnm in row.columns and pd.notnull(row.iloc[0][colnm]) and str(row.iloc[0][colnm]).strip() != ''
            ])

            if df_display.empty:
                st.info("2026학년도 모집 관련 정보가 없습니다.")
            else:
                # ✅ key 추가
                st.dataframe(df_display, hide_index=True, width=1000, key=f"df_{i}")


# =========================== #
# 6. 세로 구분선 (점선)
# =========================== #

for idx in [1, 3]:
    with cols[idx]:
        st.markdown(
            "<div style='height:130vh; border-right:2px dashed #e0e0e0; margin:0 0 0 auto'></div>",
            unsafe_allow_html=True
        )

