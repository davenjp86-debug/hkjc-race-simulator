import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（自訂賽事版）")
st.caption("手機友好版 - 自由調檔位 + 自由改評分")

# ==================== 自訂賽事 ====================
st.subheader("📝 自訂賽事設定")

num_horses = st.slider("出賽馬匹數量（5\~40匹）", min_value=5, max_value=40, value=14, step=1)
race_name = st.text_input("賽事名稱", value="沙田 第五班 1800米")

if st.button("🚀 生成賽事", type="primary"):
    st.session_state['num_horses'] = num_horses
    st.session_state['race_name'] = race_name
    st.session_state['generated'] = True
    
    # 初始化資料
    data = []
    for i in range(1, num_horses + 1):
        data.append({
            "馬號": i,
            "檔位": i,
            "狀態": "出賽",
            "評分": np.random.randint(70, 90)
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    race = st.session_state['race_name']
    df = st.session_state['df']
    
    st.subheader(f"📋 {race}（{len(df)}匹馬）")
    
    # 顯示表格
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("✏️ 編輯馬匹資料")
    
    # 選擇馬號
    horse_num = st.selectbox("選擇馬號", df['馬號'].tolist(), key="horse_select")
    
    # 取得目前資料
    current = df[df['馬號'] == horse_num].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_draw = st.number_input(
            "檔位（1-40）", 
            min_value=1, 
            max_value=40, 
            value=int(current['檔位']),
            step=1,
            key="draw_input"
        )
    
    with col2:
        new_rating = st.number_input(
            "評分（10-150）", 
            min_value=10, 
            max_value=150, 
            value=int(current['評分']),
            step=1,
            key="rating_input"
        )
    
    new_status = st.selectbox(
        "狀態", 
        ["出賽", "退出", "落馬"], 
        index=["出賽", "退出", "落馬"].index(current['狀態']),
        key="status_select"
    )
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '評分'] = new_rating
        df.loc[df['馬號'] == horse_num, '狀態'] = new_status
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 已更新！")
        st.rerun()
    
    # 過濾出賽馬匹
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 開始 5000 次專業模擬", type="primary"):
            active_horses['實力分'] = (active_horses['評分']/active_horses['評分'].max()*45 + 
                                       (15 - (active_horses['檔位']-1)*0.8)).round(1)
            
            results = []
            for _ in range(5000):
                times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.12 + np.random.normal(0,1.6) 
                         for _, row in active_horses.iterrows()}
                winner = min(times, key=times.get)
                results.append(winner)
            
            win = pd.Series(results).value_counts().reset_index()
            win.columns = ['馬號','勝出次數']
            win['勝率%'] = (win['勝出次數']/5000*100).round(1)
            win = win.merge(active_horses[['馬號','檔位','評分']], on='馬號').sort_values('勝率%', ascending=False)
            
            st.subheader("📈 模擬結果（Top 5）")
            st.dataframe(win.head(5)[['馬號','檔位','評分','勝率%']], use_container_width=True, hide_index=True)
            
            fig = px.bar(win.head(10), x='馬號', y='勝率%', title="模擬勝出率")
            st.plotly_chart(fig, use_container_width=True)
            
            st.success("✅ 模擬完成！")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()

st.caption("💡 操作提示：選擇馬號 → 輸入新數字 → 按更新")
