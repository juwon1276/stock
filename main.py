import streamlit as st
import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="주가 분석 대시보드", layout="wide")
st.title("📊 주요 기업 최근 1년 주가 변동 분석")
st.markdown("삼성전자, SK하이닉스, 구글, 애플의 최근 1년 주가 추이를 비교하고 분석합니다.")

# 2. 데이터 수집 설정 (최근 1년)
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365)

# 티커 심볼 매핑 (한국 주식은 .KS, 미국 주식은 심볼 그대로)
tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "구글 (Alphabet)": "GOOGL",
    "애플 (Apple)": "AAPL"
}

# 3. 데이터 로드 (캐싱을 통해 속도 최적화)
@st.cache_data
def load_data(ticker_dict, start, end):
    df_list = []
    for name, ticker in ticker_dict.items():
        data = yf.download(ticker, start=start, end=end)
        if not data.empty:
            # 수정종가(Adj Close) 기준 선택 (yfinance 버전에 따라 'Close' 사용 가능)
            close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            close_series = data[close_col].copy()
            close_series.name = name
            df_list.append(close_series)
    return pd.concat(df_list, axis=1)

with st.spinner("야후 파이낸스에서 데이터를 가져오는 중입니다..."):
    df = load_data(tickers, start_date, end_date)

# 4. 레이아웃 분할 (사이드바 또는 상단 탭 대신 메인 화면 구성)
st.subheader("📈 주가 추이 그래프")
st.caption("우측 상단 도구를 사용해 확대/축소 및 인터랙티브 조작이 가능합니다.")

# 5. Plotly 인터랙티브 그래프 생성
# 국장(원화)과 미장(달러)의 단위가 다르므로, 트렌드 비교를 위해 '기준일 대비 수익률(%)' 변환 옵션 제공
plot_type = st.radio("그래프 표시 방식", ["실제 주가 (원화/달러 각각 표시)", "기준일 대비 수익률 (%)"])

fig = go.Figure()

for company in df.columns:
    if plot_type == "기준일 대비 수익률 (%)":
        # 첫 번째 거래일 가격 기준으로 수익률 계산
        initial_price = df[company].dropna().iloc[0]
        y_values = ((df[company] - initial_price) / initial_price) * 100
        hovertemplate = f"{company}: %{{y:.2f}}%<extra></extra>"
        yaxis_title = "수익률 (%)"
    else:
        y_values = df[company]
        currency = "₩" if company in ["삼성전자", "SK하이닉스"] else "$"
        hovertemplate = f"{company}: {currency}%{{y:,.0f}}<extra></extra>"
        yaxis_title = "주가 (각국 통화)"

    fig.add_trace(go.Scatter(
        x=df.index, 
        y=y_values, 
        mode='lines', 
        name=company,
        hovertemplate=hovertemplate
    ))

fig.update_layout(
    template="plotly_dark",  # 스트림릿 클라우드와 잘 어울리는 다크 테마
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title=yaxis_title,
    margin=dict(l=40, r=40, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# 6. 데이터 분석 및 요약 표
st.markdown("---")
st.subheader("🔍 기업별 요약 통계 (최근 1년)")

summary_data = []
for company in df.columns:
    comp_data = df[company].dropna()
    if not comp_data.empty:
        start_p = comp_data.iloc[0]
        end_p = comp_data.iloc[-1]
        highest = comp_data.max()
        lowest = comp_data.min()
        total_return = ((end_p - start_p) / start_p) * 100
        
        currency = "원" if company in ["삼성전자", "SK하이닉스"] else "달러"
        
        summary_data.append({
            "기업명": company,
            "시작일 주가": f"{start_p:,.0f} {currency}",
            "최근 주가": f"{end_p:,.0f} {currency}",
            "최고가": f"{highest:,.0f} {currency}",
            "최저가": f"{lowest:,.0f} {currency}",
            "1년 총수익률": f"{total_return:+.2f}%"
        })

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True, hide_index=True)
