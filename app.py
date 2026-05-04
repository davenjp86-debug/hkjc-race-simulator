import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（自訂賽事版）")
st.caption("支援實力欄位")

# ==================== 自訂賽事 ====================
st.subheader("📝 自訂賽事設定")

num_horses = st.slider("出賽馬匹數量（5\~40匹）", min_value=5, max_value=40, value=14, step=1)
race_name = st.text_input("賽事名稱", value="沙田 第五班 1800米")

if st.button("🚀 生成賽事", type="primary"):
    st.session_state['num_horses'] = num_horses
    st.session_state['race_name'] = race_name
    st.session_state['generated'] = True
    
    data = []
    for i in range(1, num_horses + 1):
        data.append({
            "馬號": i,
            "檔位": None,
            "負磅": None,
            "狀態": "出賽",
            "評分": None,
            "騎師質量": None,
            "近況": None,
            "穩定": None,
            "跑法": "",
            "實力": None
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    race = st.session_state['race_name']
    df = st.session_state['df']
    
    st.subheader(f"📋 {race}（{len(df)}匹馬）")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("✏️ 編輯馬匹資料")
    
    horse_num = st.selectbox("選擇馬號", df['馬號'].tolist())
    current = df[df['馬號'] == horse_num].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        new_draw = st.number_input("檔位（1-40）", min_value=1, max_value=40, value=int(current['檔位']) if pd.notna(current['檔位']) else 1, step=1)
    with col2:
        new_weight = st.number_input("負磅（100-140）", min_value=100, max_value=140, value=int(current['負磅']) if pd.notna(current['負磅']) else 120, step=1)
    with col3:
        new_rating = st.number_input("評分（10-150）", min_value=10, max_value=150, value=int(current['評分']) if pd.notna(current['評分']) else 80, step=1)
    with col4:
        new_jockey = st.number_input("騎師質量（1-10）", min_value=1, max_value=10, value=int(current['騎師質量']) if pd.notna(current['騎師質量']) else 5, step=1)
    with col5:
        new_power = st.number_input("實力（1-100）", min_value=1, max_value=100, value=int(current['實力']) if pd.notna(current['實力']) else 50, step=1)
    
    new_status = st.selectbox("狀態", ["出賽", "退出", "落馬"], index=["出賽", "退出", "落馬"].index(current['狀態']))
    
    running_styles = ["🏹 大逃", "🏹 逃放", "🏹 前置", "🏹 先行", "🏹 居中", "🏹 中後", "🏹 留後", "🏹 後上", "🏹 後追"]
    current_run = current['跑法'].split(", ") if current['跑法'] else []
    selected_styles = st.multiselect("跑法（可多選）", running_styles, default=current_run)
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '負磅'] = new_weight
        df.loc[df['馬號'] == horse_num, '評分'] = new_rating
        df.loc[df['馬號'] == horse_num, '騎師質量'] = new_jockey
        df.loc[df['馬號'] == horse_num, '實力'] = new_power
        df.loc[df['馬號'] == horse_num, '狀態'] = new_status
        df.loc[df['馬號'] == horse_num, '跑法'] = ", ".join(selected_styles) if selected_styles else ""
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 已更新！")
        st.rerun()
    
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 開始 5000 次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '評分', '負磅', '騎師質量', '近況', '穩定', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                valid_horses['實力分'] = (
                    valid_horses['實力'] * 0.35 +
                    valid_horses['評分']/valid_horses['評分'].max()*25 + 
                    (15 - (valid_horses['檔位']-1)*0.5) +
                    (valid_horses['負磅'] - 120) * -0.08 +
                    valid_horses['騎師質量'] * 1.8 +
                    valid_horses['近況'] * 1.4 +
                    valid_horses['穩定'] * 1.1 +
                    valid_horses['跑法'].apply(lambda x: len(str(x).split(", ")) * 1.0 if pd.notna(x) and str(x) else 0)
                ).round(1)
                
                results = []
                for _ in range(5000):
                    times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.1 + np.random.normal(0,1.2) 
                             for _, row in valid_horses.iterrows()}
                    winner = min(times, key=times.get)
                    results.append(winner)
                
                win = pd.Series(results).value_counts().reset_index()
                win.columns = ['馬號','勝出次數']
                win['勝率%'] = (win['勝出次數']/5000*100).round(1)
                win = win.merge(valid_horses[['馬號','檔位','負磅','評分','實力','跑法']], on='馬號').sort_values('勝率%', ascending=False)
                
                st.subheader("📈 模擬結果（Top 5）")
                st.dataframe(win.head(5)[['馬號','檔位','負磅','評分','實力','跑法','勝率%']], use_container_width=True, hide_index=True)
                
                fig = px.bar(win.head(10), x='馬號', y='勝率%', title="模擬勝出率")
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ 模擬完成！")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()

st.caption("💡 呢個版本第一次輸入就有效！")
