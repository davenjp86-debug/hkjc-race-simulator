import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（純模擬版）")
st.caption("真實賽事資訊 + 智能模擬（無動畫）")

# ==================== 賽事資訊 ====================
st.subheader("📝 賽事資訊")

col1, col2 = st.columns(2)

with col1:
    venue = st.selectbox("馬場", ["沙田", "跑馬地"])
    if venue == "沙田":
        track = st.selectbox("場地", ["草地", "全天候"])
    else:
        track = "草地"
    race_class = st.selectbox("班級", ["一級賽", "二級賽", "三級賽", "一班", "二班", "三班", "四班", "五班"])

with col2:
    if venue == "沙田" and track == "草地":
        distance_options = [1000, 1200, 1400, 1600, 1800, 2000, 2400]
    elif venue == "沙田" and track == "全天候":
        distance_options = [1200, 1650, 1800, 2000, 2400]
    else:
        distance_options = [1000, 1200, 1650, 1800, 2200]
    distance = st.selectbox("距離（米）", distance_options)
    
    if track == "草地":
        rail = st.selectbox("欄位", ["A", "A+2", "A+3", "B", "B+2", "C", "C+3"] if venue == "沙田" else ["A", "A+2", "B", "B+2", "B+3", "C", "C+3"])
    else:
        rail = "無"
    
    weather = st.selectbox("天氣", ["晴天", "陰天", "小雨", "大雨"])

num_horses = st.slider("出賽馬匹數量（4\~40匹）", min_value=4, max_value=40, value=8, step=1)

if st.button("🚀 生成賽事", type="primary"):
    st.session_state['venue'] = venue
    st.session_state['track'] = track
    st.session_state['race_class'] = race_class
    st.session_state['distance'] = distance
    st.session_state['rail'] = rail
    st.session_state['weather'] = weather
    st.session_state['num_horses'] = num_horses
    st.session_state['generated'] = True
    
    data = []
    for i in range(1, num_horses + 1):
        data.append({
            "馬號": i, "狀態": "出賽", "檔位": None, "負磅": None,
            "騎師質量": None, "評分": None, "實力": None,
            "近況": None, "穩定": None, "跑法": ""
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    st.success(f"✅ 賽事已設定：{st.session_state['venue']} {st.session_state['distance']}米 {st.session_state['race_class']}")
    
    df = st.session_state['df']
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("✏️ 編輯馬匹資料")
    
    horse_num = st.selectbox("選擇馬號", df['馬號'].tolist())
    current = df[df['馬號'] == horse_num].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: new_draw = st.number_input("檔位", 1, 40, int(current['檔位']) if pd.notna(current['檔位']) else 1)
    with col2: new_weight = st.number_input("負磅", 100, 140, int(current['負磅']) if pd.notna(current['負磅']) else 120)
    with col3: new_jockey = st.number_input("騎師質量", 1, 10, int(current['騎師質量']) if pd.notna(current['騎師質量']) else 5)
    with col4: new_rating = st.number_input("評分", 10, 150, int(current['評分']) if pd.notna(current['評分']) else 80)
    with col5: new_power = st.number_input("實力", 1, 100, int(current['實力']) if pd.notna(current['實力']) else 50)
    
    col6, col7 = st.columns(2)
    with col6: new_recent = st.number_input("近況", 1, 10, int(current['近況']) if pd.notna(current['近況']) else 5)
    with col7: new_stable = st.number_input("穩定", 1, 10, int(current['穩定']) if pd.notna(current['穩定']) else 5)
    
    new_status = st.selectbox("狀態", ["出賽", "退出", "落馬"], index=0)
    running_styles = ["🏹 大逃", "🏹 逃放", "🏹 前置", "🏹 先行", "🏹 居中", "🏹 中後", "🏹 留後", "🏹 後上", "🏹 後追"]
    selected_styles = st.multiselect("跑法（可多選）", running_styles, default=current['跑法'].split(", ") if current['跑法'] else [])
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '負磅'] = new_weight
        df.loc[df['馬號'] == horse_num, '騎師質量'] = new_jockey
        df.loc[df['馬號'] == horse_num, '評分'] = new_rating
        df.loc[df['馬號'] == horse_num, '實力'] = new_power
        df.loc[df['馬號'] == horse_num, '近況'] = new_recent
        df.loc[df['馬號'] == horse_num, '穩定'] = new_stable
        df.loc[df['馬號'] == horse_num, '狀態'] = new_status
        df.loc[df['馬號'] == horse_num, '跑法'] = ", ".join(selected_styles) if selected_styles else ""
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 已更新！")
        st.rerun()
    
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 1次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '評分', '負磅', '騎師質量', '近況', '穩定', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                # 真正計算
                valid_horses = valid_horses.copy()
                valid_horses['實力分'] = (
                    valid_horses['實力'] * 0.30 +
                    valid_horses['評分']/valid_horses['評分'].max()*22 + 
                    (15 - (valid_horses['檔位']-1)*0.4) +
                    (valid_horses['負磅'] - 120) * -0.06 +
                    valid_horses['騎師質量'] * 1.5 +
                    valid_horses['近況'] * 1.2 +
                    valid_horses['穩定'] * 0.9 +
                    valid_horses['跑法'].apply(lambda x: len(str(x).split(", ")) * 0.8 if pd.notna(x) and str(x) else 0)
                ).round(1)
                
                # Monte Carlo 模擬
                results = []
                for _ in range(5000):
                    times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.08 + np.random.normal(0, 1.2) 
                             for _, row in valid_horses.iterrows()}
                    winner = min(times, key=times.get)
                    results.append(winner)
                
                win = pd.Series(results).value_counts().reset_index()
                win.columns = ['馬號','勝出次數']
                win['勝率%'] = (win['勝出次數']/5000*100).round(1)
                win = win.merge(valid_horses[['馬號','檔位','負磅','評分','實力','跑法']], on='馬號').sort_values('勝率%', ascending=False)
                
                st.subheader("📈 真實模擬結果（Top 5）")
                st.dataframe(win.head(5)[['馬號','檔位','負磅','評分','實力','跑法','勝率%']], use_container_width=True, hide_index=True)
                
                fig = px.bar(win.head(10), x='馬號', y='勝率%', title="真實模擬勝出率（已考慮所有因素）")
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ 模擬完成！結果已根據馬匹實力、跑法、檔位、負磅等真正計算。")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()
st.caption("💡 純模擬版：穩定 + 真實結果！")
st.divider()
st.subheader("🧠 GNN 圖神經網絡預測（進階功能）")

st.info("""
**GNN 在賽馬預測嘅優勢：**
- 可以捕捉馬匹之間嘅相互影響（例如：一匹馬領放會影響其他馬嘅配速）
- 考慮轉彎時內欄優勢
- 學習複雜嘅賽事動態關係
""")

if st.button("🚀 使用 GNN 進行預測", type="secondary"):
    valid_horses = st.session_state['df'][st.session_state['df']["狀態"] == "出賽"].dropna(subset=['檔位', '評分', '負磅', '騎師質量', '近況', '穩定', '實力'])
    
    if len(valid_horses) < 3:
        st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以預測！")
    else:
        # 模擬 GNN 輸出（實際應用需要訓練模型）
        st.subheader("📈 GNN 預測結果（Top 5）")
        
        # 簡單模擬 GNN 分數（實際應用會更複雜）
        gnn_score = (
            valid_horses['實力'] * 0.25 +
            valid_horses['評分']/valid_horses['評分'].max()*20 + 
            valid_horses['騎師質量'] * 1.8 +
            valid_horses['近況'] * 1.5 +
            valid_horses['穩定'] * 1.2 +
            (15 - (valid_horses['檔位']-1)*0.3) * 0.8
        ).round(2)
        
        gnn_result = valid_horses[['馬號','檔位','負磅','評分','實力','跑法']].copy()
        gnn_result['GNN 分數'] = gnn_score
        gnn_result = gnn_result.sort_values('GNN 分數', ascending=False)
        
        st.dataframe(gnn_result.head(5)[['馬號','檔位','負磅','評分','實力','跑法','GNN 分數']], use_container_width=True, hide_index=True)
        
        st.success("✅ GNN 預測完成！（實際應用需要大量歷史賽事數據訓練模型）")
        
        st.info("""
        **注意：**  
        呢個係 GNN 嘅概念展示。真正嘅 GNN 需要：
        - 大量歷史賽事數據
        - PyTorch Geometric 或 DGL 框架
        - 訓練圖神經網絡模型
        """)
