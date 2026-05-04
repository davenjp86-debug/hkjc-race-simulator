import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（自訂賽事版）")
st.caption("跑法支援多選")

# ==================== 自訂賽事 ====================
st.subheader("📝 自訂賽事設定")

num_horses = st.slider("出賽馬匹數量（5\~40匹）", min_value=5, max_value=40, value=14, step=1)
race_name = st.text_input("賽事名稱", value="沙田 第五班 1800米")

if st.button("🚀 生成賽事表格", type="primary"):
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
            "跑法": ""
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    race = st.session_state['race_name']
    df = st.session_state['df']
    
    st.subheader(f"📋 {race}（{len(df)}匹馬）")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("🏹 編輯跑法（可多選）")
    
    horse_num = st.selectbox("選擇馬號", df['馬號'].tolist())
    current_run = df[df['馬號'] == horse_num]['跑法'].values[0]
    
    running_styles = [
        "🏹 大逃",
        "🏹 逃放", 
        "🏹 前置",
        "🏹 先行",
        "🏹 居中",
        "🏹 中後",
        "🏹 留後",
        "🏹 後上",
        "🏹 後追"
    ]
    
    # 多選
    selected_styles = st.multiselect(
        "選擇跑法（可多選）",
        running_styles,
        default=current_run.split(", ") if current_run else []
    )
    
    if st.button("💾 更新跑法", type="primary"):
        new_run = ", ".join(selected_styles) if selected_styles else ""
        df.loc[df['馬號'] == horse_num, '跑法'] = new_run
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 跑法已更新！")
        st.rerun()
    
    if st.button("💾 儲存所有更改", type="secondary"):
        st.session_state['df'] = df
        st.success("✅ 所有更改已儲存！")
    
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 開始 5000 次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '評分', '負磅', '騎師質量', '近況', '穩定'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                valid_horses['實力分'] = (
                    valid_horses['評分']/valid_horses['評分'].max()*32 + 
                    (15 - (valid_horses['檔位']-1)*0.55) +
                    (valid_horses['負磅'] - 120) * -0.1 +
                    valid_horses['騎師質量'] * 2.0 +
                    valid_horses['近況'] * 1.6 +
                    valid_horses['穩定'] * 1.3 +
                    valid_horses['跑法'].apply(lambda x: len(str(x).split(", ")) * 1.2 if pd.notna(x) and str(x) else 0)
                ).round(1)
                
                results = []
                for _ in range(5000):
                    times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.1 + np.random.normal(0,1.3) 
                             for _, row in valid_horses.iterrows()}
                    winner = min(times, key=times.get)
                    results.append(winner)
                
                win = pd.Series(results).value_counts().reset_index()
                win.columns = ['馬號','勝出次數']
                win['勝率%'] = (win['勝出次數']/5000*100).round(1)
                win = win.merge(valid_horses[['馬號','檔位','負磅','評分','跑法']], on='馬號').sort_values('勝率%', ascending=False)
                
                st.subheader("📈 模擬結果（Top 5）")
                st.dataframe(win.head(5)[['馬號','檔位','負磅','評分','跑法','勝率%']], use_container_width=True, hide_index=True)
                
                fig = px.bar(win.head(10), x='馬號', y='勝率%', title="模擬勝出率")
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ 模擬完成！")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()

st.caption("💡 操作提示：選擇馬號 → 勾選多個跑法 → 按「更新跑法」")
