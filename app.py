import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（自訂賽事版）")
st.caption("支援手動輸入網址抓取真實賽事資料")

# ==================== 自訂 URL 抓取 ====================
st.subheader("🔗 自訂賽事網址抓取")

url_input = st.text_input("請貼上 HKJC 賽事網址（例如：https://racing.hkjc.com/racing/information/Chinese/Racing/LocalRaceCard.aspx）")

if st.button("📥 抓取資料", type="primary"):
    if url_input:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url_input, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 簡單解析（可根據實際網頁結構優化）
            st.success("✅ 成功抓取網頁！（目前使用範例資料展示，實際可根據網頁結構優化解析）")
            
            # 暫時顯示範例資料（之後可改成真正解析）
            st.info("提示：目前顯示範例資料。想即時顯示真實資料，可再告訴我網頁結構，我會優化解析器。")
            
        except Exception as e:
            st.error(f"抓取失敗：{str(e)}")
            st.info("請確認網址正確，或稍後再試。")
    else:
        st.warning("請輸入網址！")

st.divider()

# ==================== 場次選擇器 ====================
st.subheader("🏁 快速選擇真實賽事（範例資料）")

race_options = {
    "沙田 全天候 19/4/26 第五班 1800米（14匹）": "race1",
    "沙田  turf  20/4/26 第三班 1400米（12匹）": "race2",
    "跑馬地  turf  21/4/26 第四班 1200米（10匹）": "race3",
    "沙田 全天候 22/4/26 第二班 1650米（9匹）": "race4",
    "跑馬地  turf  23/4/26 第五班 1800米（8匹）": "race5"
}

selected_race = st.selectbox("選擇場次", list(race_options.keys()))

# 真實資料（同之前版本）
race_data = { ... }  # 省略，保持之前嘅 race_data

df = pd.DataFrame(race_data[race_options[selected_race]])

# 計算實力分
df['實力分'] = (df['評分']/df['評分'].max()*45 + 
                (30 - df['近績'].apply(lambda x: np.mean([int(i) for i in str(x).split('/') if i.isdigit()]))*3.5) + 
                (15 - (df['檔位']-1)*1.2)).round(1)

st.subheader(f"📋 {selected_race}")
st.dataframe(df[['馬號','馬名','檔位','負磅','評分','狀態','最佳路程','實力分']], use_container_width=True, hide_index=True)

# 模擬
if st.button("🚀 開始 5000 次專業模擬", type="primary"):
    results = []
    for _ in range(5000):
        times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.15 + np.random.normal(0,1.8) 
                 for _, row in df.iterrows()}
        sorted_h = sorted(times.items(), key=lambda x: x[1])
        results.append(sorted_h[0][0])
    
    win = pd.Series(results).value_counts().reset_index()
    win.columns = ['馬號','勝出次數']
    win['勝率%'] = (win['勝出次數']/5000*100).round(1)
    win = win.merge(df[['馬號','馬名']], on='馬號').sort_values('勝率%', ascending=False)
    
    st.subheader("📈 模擬結果（Top 5）")
    st.dataframe(win.head(5)[['馬名','勝率%']], use_container_width=True, hide_index=True)
    
    fig = px.bar(win.head(8), x='馬名', y='勝率%', title="模擬勝出率")
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("✅ 模擬完成！")

st.caption("💡 提示：用手機 Chrome 開啟後，點擊右上角 ⋮ → 「加入主畫面」即可安裝做 App")
