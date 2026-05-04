import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終版）")
st.caption("直接喺表格編輯 + 儲存按鈕（解決第一次輸入變 None 問題）")

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
            "狀態": "出賽",
            "評分": None
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    race = st.session_state['race_name']
    df = st.session_state['df']
    
    st.subheader(f"📋 {race}（{len(df)}匹馬）")
    st.caption("編輯完後 → 請按下面「儲存更改」按鈕")
    
    # 可編輯表格
    edited_df = st.data_editor(
        df,
        column_config={
            "馬號": st.column_config.NumberColumn("馬號", disabled=True),
            "檔位": st.column_config.NumberColumn("檔位", min_value=1, max_value=40),
            "狀態": st.column_config.SelectboxColumn("狀態", options=["出賽", "退出", "落馬"]),
            "評分": st.column_config.NumberColumn("評分", min_value=10, max_value=150)
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )
    
    # 儲存更改按鈕（解決第一次輸入變 None 問題）
    if st.button("💾 儲存更改", type="primary"):
        st.session_state['df'] = edited_df
        st.success("✅ 更改已儲存！")
        st.rerun()
    
    # 過濾出賽馬匹
    active_horses = edited_df[edited_df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 開始 5000 次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '評分'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫檔位同評分先可以模擬！")
            else:
                valid_horses['實力分'] = (valid_horses['評分']/valid_horses['評分'].max()*45 + 
                                          (15 - (valid_horses['檔位']-1)*0.8)).round(1)
                
                results = []
                for _ in range(5000):
                    times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.12 + np.random.normal(0,1.6) 
                             for _, row in valid_horses.iterrows()}
                    winner = min(times, key=times.get)
                    results.append(winner)
                
                win = pd.Series(results).value_counts().reset_index()
                win.columns = ['馬號','勝出次數']
                win['勝率%'] = (win['勝出次數']/5000*100).round(1)
                win = win.merge(valid_horses[['馬號','檔位','評分']], on='馬號').sort_values('勝率%', ascending=False)
                
                st.subheader("📈 模擬結果（Top 5）")
                st.dataframe(win.head(5)[['馬號','檔位','評分','勝率%']], use_container_width=True, hide_index=True)
                
                fig = px.bar(win.head(10), x='馬號', y='勝率%', title="模擬勝出率")
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ 模擬完成！")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()

st.caption("💡 操作提示：編輯完表格後 → 一定要按「儲存更改」按鈕")
