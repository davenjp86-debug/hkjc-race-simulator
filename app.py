import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（自訂賽事版）")
st.caption("自訂馬匹數量 + 自由調檔位 + 模擬真實賽事")

# ==================== 自訂賽事 ====================
st.subheader("📝 自訂賽事設定")

col1, col2 = st.columns(2)
with col1:
    num_horses = st.slider("出賽馬匹數量", min_value=5, max_value=40, value=14, step=1)
with col2:
    race_name = st.text_input("賽事名稱（可選）", value="沙田 第五班 1800米")

if st.button("🚀 生成賽事表格", type="primary"):
    st.session_state['num_horses'] = num_horses
    st.session_state['race_name'] = race_name
    st.session_state['generated'] = True

if st.session_state.get('generated', False):
    num = st.session_state['num_horses']
    race = st.session_state['race_name']
    
    st.subheader(f"📋 {race}（{num}匹馬）")
    
    # 建立可編輯表格
    data = []
    for i in range(1, num + 1):
        data.append({
            "馬號": i,
            "馬名": f"馬{i}",
            "檔位": i,
            "狀態": "出賽",
            "評分": np.random.randint(60, 95)
        })
    
    df = pd.DataFrame(data)
    
    # 使用 st.data_editor 讓用戶編輯
    edited_df = st.data_editor(
        df,
        column_config={
            "馬號": st.column_config.NumberColumn("馬號", disabled=True),
            "馬名": st.column_config.TextColumn("馬名"),
            "檔位": st.column_config.NumberColumn("檔位", min_value=1, max_value=40),
            "狀態": st.column_config.SelectboxColumn("狀態", options=["出賽", "退出", "落馬"]),
            "評分": st.column_config.NumberColumn("評分", min_value=1, max_value=120)
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )
    
    # 過濾出賽馬匹
    active_horses = edited_df[edited_df["狀態"] == "出賽"].copy()
    
    if len(active_horses) < 3:
        st.error("至少需要 3 匹出賽馬先可以模擬！")
    else:
        st.success(f"✅ 目前有 {len(active_horses)} 匹馬出賽")
        
        if st.button("🚀 開始 5000 次專業模擬", type="primary"):
            # 計算實力分
            active_horses['實力分'] = (active_horses['評分']/active_horses['評分'].max()*45 + 
                                       (15 - (active_horses['檔位']-1)*0.8)).round(1)
            
            # Monte Carlo 模擬
            results = []
            for _ in range(5000):
                times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.12 + np.random.normal(0,1.6) 
                         for _, row in active_horses.iterrows()}
                winner = min(times, key=times.get)
                results.append(winner)
            
            win = pd.Series(results).value_counts().reset_index()
            win.columns = ['馬號','勝出次數']
            win['勝率%'] = (win['勝出次數']/5000*100).round(1)
            win = win.merge(active_horses[['馬號','馬名','檔位']], on='馬號').sort_values('勝率%', ascending=False)
            
            st.subheader("📈 模擬結果（Top 5）")
            st.dataframe(win.head(5)[['馬名','檔位','勝率%']], use_container_width=True, hide_index=True)
            
            fig = px.bar(win.head(10), x='馬名', y='勝率%', title="模擬勝出率")
            st.plotly_chart(fig, use_container_width=True)
            
            st.success("✅ 模擬完成！")

st.divider()

st.caption("💡 提示：用手機 Chrome 開啟後，點擊右上角 ⋮ → 「加入主畫面」即可安裝做 App")
