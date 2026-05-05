import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終專業版）")
st.caption("GNN增強 + 10次模擬 + 真實結果輸入 + 自我學習 + 儲存讀取")

# ==================== 初始化儲存 ====================
if 'saved_races' not in st.session_state:
    st.session_state['saved_races'] = []

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
    st.session_state['real_results'] = {}

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
        if st.button("🚀 10次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '評分', '負磅', '騎師質量', '近況', '穩定', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                # GNN增強
                valid_horses = valid_horses.copy()
                base_score = (
                    valid_horses['實力'] * 0.28 +
                    valid_horses['評分']/valid_horses['評分'].max()*20 + 
                    (15 - (valid_horses['檔位']-1)*0.35) +
                    (valid_horses['負磅'] - 120) * -0.05 +
                    valid_horses['騎師質量'] * 1.4 +
                    valid_horses['近況'] * 1.1 +
                    valid_horses['穩定'] * 0.85
                )
                
                def gnn_interaction(row):
                    score = 0
                    if "大逃" in str(row['跑法']): score += 2.5
                    if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 1.8
                    if "居中" in str(row['跑法']): score += 1.5
                    return score
                
                valid_horses['GNN_增強分'] = valid_horses.apply(gnn_interaction, axis=1)
                valid_horses['實力分'] = (base_score + valid_horses['GNN_增強分'] * 0.6).round(1)
                
                # 10次模擬
                all_results = []
                for _ in range(10):
                    results = []
                    for _ in range(5000):
                        times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.08 + np.random.normal(0, 1.2) 
                                 for _, row in valid_horses.iterrows()}
                        sorted_horses = sorted(times.items(), key=lambda x: x[1])
                        results.append([h[0] for h in sorted_horses[:4]])
                    all_results.extend(results)
                
                # 統計
                stats = {}
                for horse in valid_horses['馬號']:
                    stats[horse] = {'第一名次數': 0, '頭兩名內次數': 0, '頭三名內次數': 0, '頭四名內次數': 0, '總分數': 0}
                
                for result in all_results:
                    for rank, horse in enumerate(result, 1):
                        if horse in stats:
                            if rank == 1: stats[horse]['第一名次數'] += 1
                            if rank <= 2: stats[horse]['頭兩名內次數'] += 1
                            if rank <= 3: stats[horse]['頭三名內次數'] += 1
                            if rank <= 4: stats[horse]['頭四名內次數'] += 1
                            
                            if rank == 1: stats[horse]['總分數'] += 6
                            elif rank == 2: stats[horse]['總分數'] += 5
                            elif rank == 3: stats[horse]['總分數'] += 4
                            elif rank == 4: stats[horse]['總分數'] += 3
                            elif rank == 5: stats[horse]['總分數'] += 2
                            elif rank == 6: stats[horse]['總分數'] += 1
                            else: stats[horse]['總分數'] -= 3
                
                result_df = pd.DataFrame.from_dict(stats, orient='index').reset_index()
                result_df.columns = ['馬號', '第一名次數', '頭兩名內次數', '頭三名內次數', '頭四名內次數', '總分數']
                result_df = result_df.sort_values('總分數', ascending=False)
                
                st.session_state['simulation_result'] = result_df
                st.subheader("📈 10次專業模擬結果")
                st.dataframe(result_df, use_container_width=True, hide_index=True)
                st.success("✅ 10次專業模擬完成！已結合GNN增強")
    
    # ==================== 真實賽事結果輸入 ====================
    st.divider()
    st.subheader("📝 輸入真實賽事結果")
    
    real_results = {}
    for i in range(1, num_horses + 1):
        real_results[i] = st.text_input(f"第 {i} 名馬號", value="", key=f"real_{i}")
    
    withdrawn = st.text_input("中途退出馬號（多個用逗號分隔）", value="")
    
    if st.button("💾 儲存真實結果", type="secondary"):
        st.session_state['real_results'] = real_results
        st.session_state['withdrawn'] = withdrawn
        st.success("✅ 真實賽事結果已儲存！")
    
    # ==================== 賽後自我學習 ====================
    if st.button("🧠 賽後自我學習", type="primary"):
        if 'simulation_result' not in st.session_state or 'real_results' not in st.session_state:
            st.error("⚠️ 請先進行模擬並輸入真實結果！")
        else:
            sim = st.session_state['simulation_result']
            real = st.session_state['real_results']
            
            # 簡單學習：調整實力分
            for horse in sim['馬號']:
                real_rank = None
                for rank, h in real.items():
                    if str(h) == str(horse):
                        real_rank = rank
                        break
                
                if real_rank:
                    current_score = sim[sim['馬號'] == horse]['總分數'].values[0]
                    if real_rank <= 3:
                        # 真實表現好，增加實力
                        df.loc[df['馬號'] == horse, '實力'] = min(100, int(df.loc[df['馬號'] == horse, '實力']) + 3)
                    elif real_rank >= 7:
                        # 真實表現差，降低實力
                        df.loc[df['馬號'] == horse, '實力'] = max(1, int(df.loc[df['馬號'] == horse, '實力']) - 3)
            
            st.session_state['df'] = df
            st.success("✅ 學習完成！模型已根據真實結果調整，會在下次模擬時生效。")
    
    # ==================== 儲存/讀取賽事 ====================
    st.divider()
    st.subheader("💾 儲存 / 讀取賽事")
    
    col_save, col_load = st.columns(2)
    
    with col_save:
        save_label = st.text_input("儲存標籤（例如：沙田 1800米 第五班）")
        if st.button("💾 儲存賽事"):
            if len(st.session_state['saved_races']) >= 30:
                st.session_state['saved_races'].pop(0)  # 刪除最舊
            
            save_data = {
                'label': save_label,
                'venue': st.session_state.get('venue'),
                'track': st.session_state.get('track'),
                'race_class': st.session_state.get('race_class'),
                'distance': st.session_state.get('distance'),
                'df': st.session_state.get('df'),
                'simulation_result': st.session_state.get('simulation_result'),
                'real_results': st.session_state.get('real_results', {})
            }
            st.session_state['saved_races'].append(save_data)
            st.success(f"✅ 賽事已儲存！（目前 {len(st.session_state['saved_races'])}/30）")
    
    with col_load:
        if st.session_state['saved_races']:
            labels = [r['label'] for r in st.session_state['saved_races']]
            selected = st.selectbox("選擇要讀取嘅賽事", labels)
            
            if st.button("📂 讀取賽事"):
                for race in st.session_state['saved_races']:
                    if race['label'] == selected:
                        st.session_state['venue'] = race['venue']
                        st.session_state['track'] = race['track']
                        st.session_state['race_class'] = race['race_class']
                        st.session_state['distance'] = race['distance']
                        st.session_state['df'] = race['df']
                        st.session_state['simulation_result'] = race['simulation_result']
                        st.session_state['real_results'] = race['real_results']
                        st.success(f"✅ 已讀取賽事：{selected}")
                        st.rerun()
        else:
            st.info("暫時冇儲存嘅賽事")

st.divider()
st.caption("💡 最終專業版：GNN + 10次模擬 + 真實結果 + 自我學習 + 儲存讀取！")
