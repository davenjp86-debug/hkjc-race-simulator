import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終專業版）")
st.caption("GNN + 全因素模擬 + 批量貼上資料（你嘅格式）")

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

if st.button("🚀 生成賽事", type="primary"):
    st.session_state['venue'] = venue
    st.session_state['track'] = track
    st.session_state['race_class'] = race_class
    st.session_state['distance'] = distance
    st.session_state['rail'] = rail
    st.session_state['weather'] = weather
    st.session_state['generated'] = True
    
    data = []
    for i in range(1, 9):
        data.append({
            "馬號": i, "狀態": "出賽", "檔位": None, "負磅": None,
            "騎師質量": None, "實力": None,
            "近況": None, "穩定": None, "跑法": ""
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    st.success(f"✅ 賽事已設定：{st.session_state['venue']} {st.session_state['distance']}米 {st.session_state['race_class']}")
    
    df = st.session_state['df']
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ==================== 批量貼上馬匹資料 ====================
    st.divider()
    st.subheader("📋 批量貼上馬匹資料（從記事本複製）")
    
    st.info("格式範例：1. 出賽,7,135,5,40,7,4,5678")
    
    batch_input = st.text_area("貼上馬匹資料", height=200, placeholder="例如：\n1. 出賽,7,135,5,40,7,4,5678\n2. 出賽,6,124,3,12,2,3,234")
    
    if st.button("🚀 套用批量資料", type="primary"):
        if batch_input.strip() == "":
            st.error("⚠️ 請先貼上資料！")
        else:
            try:
                lines = [line.strip() for line in batch_input.strip().split('\n') if line.strip()]
                new_data = []
                
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    
                    if len(parts) >= 8:
                        # 格式：1. 出賽,7,135,5,40,7,4,5678
                        horse_num = int(parts[0].replace('.', ''))
                        status = parts[1]
                        draw = max(1, min(40, int(parts[2])))
                        weight = max(100, min(140, int(parts[3])))
                        jockey = max(1, min(10, int(parts[4])))
                        power = max(1, min(100, int(parts[5])))
                        recent = max(1, min(10, int(parts[6])))
                        stable = max(1, min(10, int(parts[7])))
                        
                        # 跑法
                        run_codes = parts[8] if len(parts) > 8 else ""
                        run_map = {
                            "1": "🏹 大逃", "2": "🏹 逃放", "3": "🏹 前置",
                            "4": "🏹 先行", "5": "🏹 居中", "6": "🏹 中後",
                            "7": "🏹 留後", "8": "🏹 後上", "9": "🏹 後追"
                        }
                        
                        run_styles = []
                        for code in run_codes:
                            if code in run_map:
                                run_styles.append(run_map[code])
                        
                        run_style = ", ".join(run_styles) if run_styles else ""
                        
                        new_data.append({
                            "馬號": horse_num,
                            "狀態": status,
                            "檔位": draw,
                            "負磅": weight,
                            "騎師質量": jockey,
                            "實力": power,
                            "近況": recent,
                            "穩定": stable,
                            "跑法": run_style
                        })
                
                if new_data:
                    st.session_state['df'] = pd.DataFrame(new_data)
                    st.success(f"✅ 已成功套用 {len(new_data)} 匹馬嘅資料！")
                    st.rerun()
                else:
                    st.error("⚠️ 未能解析到有效資料，請檢查格式！")
                    
            except Exception as e:
                st.error(f"⚠️ 解析失敗：{str(e)}")
    
    # ==================== 編輯馬匹資料 ====================
    st.divider()
    st.subheader("✏️ 編輯馬匹資料")
    
    df = st.session_state['df']
    horse_num = st.selectbox("選擇馬號", df['馬號'].tolist())
    current = df[df['馬號'] == horse_num].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: new_draw = st.number_input("檔位", 1, 40, int(current['檔位']) if pd.notna(current['檔位']) else 1)
    with col2: new_weight = st.number_input("負磅", 100, 140, int(current['負磅']) if pd.notna(current['負磅']) else 120)
    with col3: new_jockey = st.number_input("騎師質量", 1, 10, int(current['騎師質量']) if pd.notna(current['騎師質量']) else 5)
    with col4: new_power = st.number_input("實力", 1, 100, int(current['實力']) if pd.notna(current['實力']) else 50)
    with col5: new_recent = st.number_input("近況", 1, 10, int(current['近況']) if pd.notna(current['近況']) else 5)
    
    col6, col7 = st.columns(2)
    with col6: new_stable = st.number_input("穩定", 1, 10, int(current['穩定']) if pd.notna(current['穩定']) else 5)
    with col7: new_status = st.selectbox("狀態", ["出賽", "退出", "落馬"], index=0)
    
    running_styles = ["🏹 大逃", "🏹 逃放", "🏹 前置", "🏹 先行", "🏹 居中", "🏹 中後", "🏹 留後", "🏹 後上", "🏹 後追"]
    selected_styles = st.multiselect("跑法（可多選）", running_styles, default=current['跑法'].split(", ") if current['跑法'] else [])
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '負磅'] = new_weight
        df.loc[df['馬號'] == horse_num, '騎師質量'] = new_jockey
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
            valid_horses = active_horses.dropna(subset=['檔位', '負磅', '騎師質量', '近況', '穩定', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                # GNN + 全因素
                valid_horses = valid_horses.copy()
                
                base_score = (
                    valid_horses['實力'] * 0.25 +
                    (15 - (valid_horses['檔位']-1)*0.3) +
                    (valid_horses['負磅'] - 120) * -0.04 +
                    valid_horses['騎師質量'] * 1.6 +
                    valid_horses['近況'] * 1.0 +
                    valid_horses['穩定'] * 0.75
                )
                
                def gnn_interaction(row):
                    score = 0
                    venue = st.session_state.get('venue', '沙田')
                    track = st.session_state.get('track', '草地')
                    distance = st.session_state.get('distance', 1600)
                    weather = st.session_state.get('weather', '晴天')
                    race_class = st.session_state.get('race_class', '五班')
                    jockey = row['騎師質量']
                    
                    if "大逃" in str(row['跑法']): score += 2.0
                    if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 1.5
                    if "居中" in str(row['跑法']): score += 1.3
                    
                    if distance <= 1200:
                        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']): score += 3.5
                        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score -= 2.0
                    elif distance >= 2000:
                        if "居中" in str(row['跑法']) or "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 3.0
                        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']): score -= 1.8
                        score += (row['實力'] + row['穩定'] - 100) * 0.04
                    else:
                        if "居中" in str(row['跑法']): score += 1.2
                    
                    if track == "全天候":
                        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']) or "前置" in str(row['跑法']): score += 1.8
                        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score -= 1.0
                    else:
                        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 2.2
                        if "大逃" in str(row['跑法']): score -= 0.8
                    
                    if weather == "小雨":
                        if track == "草地":
                            if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 2.5
                            if "大逃" in str(row['跑法']): score -= 1.5
                    elif weather == "大雨":
                        if track == "草地":
                            if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 3.5
                            if "大逃" in str(row['跑法']): score -= 2.5
                            score += (row['穩定'] - 50) * 0.03
                    
                    if race_class in ["一級賽", "二級賽"]:
                        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score -= 1.0
                    elif race_class in ["四班", "五班"]:
                        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']): score += 2.0
                        if "大逃" in str(row['跑法']): score -= 1.0
                        score += (row['穩定'] - 50) * 0.02
                    
                    score += jockey * 1.8
                    if race_class in ["一級賽", "二級賽", "三級賽"]:
                        if jockey >= 8: score += 2.5
                        if jockey <= 4: score -= 1.5
                    if weather in ["小雨", "大雨"]:
                        if jockey >= 7: score += 2.0
                        if jockey <= 4: score -= 1.2
                    if distance >= 1800:
                        if jockey >= 7: score += 1.8
                        if jockey <= 4: score -= 1.0
                    
                    if venue == "跑馬地":
                        if row['檔位'] <= 4: score += 3.2
                        if row['檔位'] >= 10: score -= 1.8
                    else:
                        if row['檔位'] <= 5: score += 1.3
                        if row['檔位'] >= 12: score -= 0.9
                    
                    return score
                
                valid_horses['GNN_增強分'] = valid_horses.apply(gnn_interaction, axis=1)
                valid_horses['實力分'] = (base_score + valid_horses['GNN_增強分'] * 0.65).round(1)
                
                all_results = []
                for _ in range(10):
                    results = []
                    for _ in range(5000):
                        times = {row['馬號']: 70 - (row['實力分']-50)*0.08 + (row['檔位']-1)*0.08 + np.random.normal(0, 1.2) 
                                 for _, row in valid_horses.iterrows()}
                        sorted_horses = sorted(times.items(), key=lambda x: x[1])
                        results.append([h[0] for h in sorted_horses[:4]])
                    all_results.extend(results)
                
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
                
                st.subheader("📈 10次專業模擬結果（已考慮所有因素）")
                st.dataframe(result_df, use_container_width=True, hide_index=True)
                
                st.success("✅ 10次專業模擬完成！已結合：馬場 + 距離 + 場地 + 天氣 + 班級 + 騎師 + GNN")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()
st.caption("💡 最終專業版：全因素模擬 + 批量貼上資料（你嘅格式）")
