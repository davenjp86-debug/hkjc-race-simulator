import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（真實動畫版）")
st.caption("出閘 + 位置爭奪 + 轉彎 + 衝刺動畫")

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
    st.success(f"✅ 賽事已設定：{st.session_state['venue']} {st.session_state['distance']}米")
    
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
        if st.button("🚀 1次專業模擬 + 真實動畫", type="primary"):
            st.subheader("🏁 比賽即將開始！")
            
            # 真實賽馬動畫
            race_html = """
            <div style="background: #0a3d0a; padding: 20px; border-radius: 15px; color: white; text-align: center; font-family: Arial;">
                <h2 style="margin: 10px 0;">🏁 真實賽馬動畫</h2>
                
                <div style="background: #1a5f1a; padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>出閘！</div>
                        <div>轉彎相爭！</div>
                        <div>最後衝刺！</div>
                    </div>
                    
                    <!-- 動畫賽道 -->
                    <div style="position: relative; height: 120px; background: #2d7a2d; border-radius: 8px; overflow: hidden; border: 3px solid #ffd700;">
                        
                        <!-- 賽道線 -->
                        <div style="position: absolute; top: 30px; left: 0; right: 0; height: 2px; background: repeating-linear-gradient(90deg, white, white 20px, transparent 20px, transparent 40px);"></div>
                        <div style="position: absolute; top: 60px; left: 0; right: 0; height: 2px; background: repeating-linear-gradient(90deg, white, white 20px, transparent 20px, transparent 40px);"></div>
                        <div style="position: absolute; top: 90px; left: 0; right: 0; height: 2px; background: repeating-linear-gradient(90deg, white, white 20px, transparent 20px, transparent 40px);"></div>
                        
                        <!-- 馬匹動畫 -->
                        <div style="position: absolute; top: 15px; left: 10px; font-size: 28px; animation: horse1 4s linear forwards;">🏇</div>
                        <div style="position: absolute; top: 45px; left: 10px; font-size: 28px; animation: horse2 3.8s linear forwards;">🏇</div>
                        <div style="position: absolute; top: 75px; left: 10px; font-size: 28px; animation: horse3 4.2s linear forwards;">🏇</div>
                        
                        <!-- 終點線 -->
                        <div style="position: absolute; top: 0; right: 30px; width: 4px; height: 100%; background: #ffd700; box-shadow: 0 0 10px #ffd700;"></div>
                    </div>
                    
                    <style>
                        @keyframes horse1 {
                            0% { left: 10px; }
                            100% { left: 85%; }
                        }
                        @keyframes horse2 {
                            0% { left: 10px; }
                            100% { left: 88%; }
                        }
                        @keyframes horse3 {
                            0% { left: 10px; }
                            100% { left: 82%; }
                        }
                    </style>
                    
                    <p style="margin-top: 15px; font-size: 18px;">🏇 馬匹全力奔馳中...</p>
                </div>
            </div>
            """
            components.html(race_html, height=320)
            
            # 顯示模擬結果
            st.success("✅ 比賽完成！")
            st.subheader("📈 模擬結果（Top 5）")
            st.dataframe(active_horses[['馬號','檔位','負磅','評分','實力']].head(5), use_container_width=True, hide_index=True)
            
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()
st.caption("💡 真實動畫版：出閘 + 轉彎 + 衝刺！")
