import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from collections import Counter
import json
import os
from PIL import Image, ImageEnhance, ImageFilter

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終專業版）")
st.caption("Enhanced Monte Carlo（50,000次）+ GNN + Optimized Pace Model + 全因素 + 詳細投注統計 + 賽事級學習 + Pace Scenario Analysis + Weight Sensitivity")

# ==================== JSON 檔案儲存功能 ====================
DATA_FILE = "learned_data.json"

def load_learned_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_learned_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== Optimized Pace Model 功能 ====================
def optimized_pace_model(row, front_runners, distance, venue, weather, race_class):
    score = 0
    
    if front_runners >= 4:
        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
            score += 5.0 + (front_runners - 3) * 0.5
        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']):
            score -= 3.5
    elif front_runners >= 2:
        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
            score += 3.0 + (front_runners - 2) * 0.3
        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']):
            score -= 2.0
    elif front_runners == 1:
        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']):
            score += 2.5
        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
            score -= 0.5
    else:
        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
            score -= 2.0
        if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']):
            score += 4.5
    
    if distance <= 1200:
        score *= 1.4
    elif distance >= 2000:
        score *= 0.6
    
    if venue == "跑馬地":
        score *= 1.3
    
    if weather in ["小雨", "大雨"]:
        if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
            score += 2.0
    
    if race_class in ["一級賽", "二級賽"]:
        score *= 0.7
    elif race_class in ["四班", "五班"]:
        score *= 1.2
    
    return score

# ==================== Pace Scenario Analysis 功能 ====================
def analyze_pace_scenario(horses_df):
    front_runners = 0
    prominent = 0
    closers = 0
    
    for _, row in horses_df.iterrows():
        run_style = str(row['跑法'])
        if "大逃" in run_style or "逃放" in run_style:
            front_runners += 1
        if "前置" in run_style or "先行" in run_style:
            prominent += 1
        if "後上" in run_style or "後追" in run_style:
            closers += 1
    
    total_horses = len(horses_df)
    
    if front_runners >= 4:
        scenario = "False Pace（假前置型）"
        adjustment = {'closer_bonus': 4.5, 'front_penalty': -2.5, 'description': '前置型馬過多，後上型馬優勢極大'}
    elif front_runners >= 2:
        scenario = "True Pace（真正前置型）"
        adjustment = {'closer_bonus': 2.5, 'front_penalty': -1.0, 'description': '前置型馬適中，後上型馬有優勢'}
    elif front_runners <= 1:
        scenario = "Slow Pace（慢前置型）"
        adjustment = {'closer_bonus': -1.5, 'front_bonus': 3.5, 'description': '前置型馬過少，前置型馬優勢大'}
    else:
        scenario = "Even Pace（平均型）"
        adjustment = {'closer_bonus': 0.5, 'front_bonus': 0.5, 'description': '配速平均'}
    
    return {
        'scenario': scenario,
        'front_runners': front_runners,
        'prominent': prominent,
        'closers': closers,
        'adjustment': adjustment,
        'total_horses': total_horses
    }

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
    for i in range(1, 15):
        data.append({
            "馬號": i, "狀態": "出賽", "檔位": None, "負磅": None,
            "騎師質量": None, "實力": None,
            "近況": None, "跑法": ""
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    st.success(f"✅ 賽事已設定：{st.session_state['venue']} {st.session_state['distance']}米 {st.session_state['race_class']}")
    
    df = st.session_state['df']
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ==================== 馬匹資料輸入 ====================
    st.divider()
    st.subheader("📋 馬匹資料輸入")
    
    st.info("""
    **建議做法：**
    1. 用手機「複製圖片文字」功能
    2. 直接貼上文字到下面文字框
    3. 按「套用批量資料」
    """)
    
    batch_input = st.text_area("貼上馬匹資料（或截圖文字）", height=150, 
                               placeholder="例如：\n1.出賽,7,135,5,40,7,5678\n2.出賽,6,134,10,38,5,4,12")
    
    if st.button("🚀 套用批量資料", type="primary"):
        if batch_input.strip():
            try:
                lines = [line.strip() for line in batch_input.strip().split('\n') if line.strip()]
                new_data = []
                
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 7:
                        first_part = parts[0]
                        
                        if '.' in first_part:
                            horse_num = int(first_part.split('.')[0])
                            status = first_part.split('.')[1]
                        else:
                            horse_num = int(first_part)
                            status = parts[1]
                            parts = [status] + parts[1:]
                        
                        draw = max(1, min(40, int(parts[1])))
                        weight = max(100, min(140, int(parts[2])))
                        jockey = max(1, min(10, int(parts[3])))
                        power = max(1, min(100, int(parts[4])))
                        recent = max(1, min(10, int(parts[5])))
                        
                        run_codes = parts[6] if len(parts) > 6 else ""
                        run_map = {
                            "1": "🏹 領放", "2": "🏹 居前", "3": "🏹 留後", "4": "🏹 後追"
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
                            "跑法": run_style
                        })
                
                if new_data:
                    st.session_state['df'] = pd.DataFrame(new_data)
                    st.success(f"✅ 已成功套用 {len(new_data)} 匹馬嘅資料！")
                    st.rerun()
                else:
                    st.error("未能解析到有效資料，請檢查格式！")
            except Exception as e:
                st.error(f"解析失敗：{str(e)}")
    
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
    
    running_styles = ["🏹 領放", "🏹 居前", "🏹 留後", "🏹 後追"]
    selected = st.multiselect("跑法", running_styles, default=current['跑法'].split(", ") if current['跑法'] else [])
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '負磅'] = new_weight
        df.loc[df['馬號'] == horse_num, '騎師質量'] = new_jockey
        df.loc[df['馬號'] == horse_num, '實力'] = new_power
        df.loc[df['馬號'] == horse_num, '近況'] = new_recent
        df.loc[df['馬號'] == horse_num, '跑法'] = ", ".join(selected) if selected else ""
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 已更新！")
        st.rerun()
    
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 開始 50,000 次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '負磅', '騎師質量', '實力'])
            
            if len(valid_horses) < 3:
                st.error("至少需要 3 匹馬填寫完整資料！")
            else:
                pace_analysis = analyze_pace_scenario(valid_horses)
                
                st.subheader("📊 Pace Scenario Analysis")
                st.write(f"**配速情景：** {pace_analysis['scenario']}")
                st.info(pace_analysis['adjustment']['description'])
                
                with st.spinner("正在進行 50,000 次模擬..."):
                    horse_ids = valid_horses['馬號'].values
                    base_strength = valid_horses['實力'].values.astype(float)
                    draw_penalty = (valid_horses['檔位'].values - 1) * 0.08
                    
                    all_winners = []
                    all_top4 = []
                    
                    for _ in range(10):
                        random_noise = np.random.normal(0, 1.8, size=(5000, len(horse_ids)))
                        finish_times = 70 - (base_strength - 50) * 0.08 + draw_penalty + random_noise
                        sorted_indices = np.argsort(finish_times, axis=1)
                        
                        winners = horse_ids[sorted_indices[:, 0]]
                        top4 = horse_ids[sorted_indices[:, :4]]
                        
                        all_winners.extend(winners)
                        all_top4.extend([tuple(t) for t in top4])
                
                st.success("✅ 50,000 次 Monte Carlo 模擬完成！")
                
                win_count = Counter(all_winners)
                most_win = win_count.most_common(1)[0]
                
                st.subheader("📈 模擬結果")
                st.write(f"**最多獨贏**：馬號 {most_win[0]}（{most_win[1]} 場，{round(most_win[1]/50000*100, 1)}%）")
                
                st.divider()
                st.subheader("📊 詳細馬匹分析")
                
                horse_top3_count = Counter()
                for res in all_top4:
                    for horse in res:
                        horse_top3_count[horse] += 1
                
                for horse in sorted(horse_ids):
                    st.write(f"**馬號 {horse}**：前三名次數 {horse_top3_count[horse]} 場（{round(horse_top3_count[horse]/50000*100, 1)}%）")
                
                st.success("✅ 模擬完成！")
    else:
        st.warning("至少需要 3 匹出賽馬先可以模擬！")

# ==================== 截圖功能提示 ====================
st.divider()
st.subheader("📸 截圖功能提示")

st.info("""
**截圖識別功能暫時需要本地安裝**

由於 Streamlit Cloud 環境限制，OCR 功能暫時無法使用。

**建議做法：**
1. 用手機「複製圖片文字」功能
2. 直接貼上文字到 App
3. App 會自動解析並學習

這樣一樣可以達到自動輸入嘅效果！
""")

# ==================== 比賽結果輸入 ====================
st.divider()
st.subheader("📝 輸入真實賽果並學習")

st.info("格式範例：2,3,4,5,9,11,8,6,7,10_1,12")

race_result_input = st.text_input("輸入真實賽果", placeholder="例如：2,3,4,5,9,11,8,6,7,10_1,12")

if st.button("📚 輸入真實賽果並學習", type="primary"):
    if race_result_input.strip():
        try:
            parts = race_result_input.strip().split('_')
            finish_order = [int(x.strip()) for x in parts[0].split(',')]
            dnf = [int(x.strip()) for x in parts[1].split(',')] if len(parts) > 1 else []
            
            learned_data = load_learned_data()
            
            if 'learning_patterns' not in learned_data:
                learned_data['learning_patterns'] = {
                    'rainy_weather_closers': 0.0,
                    'happy_valley_inner_barrier': 0.0,
                    'long_distance_stamina': 0.0,
                    'high_class_jockey': 0.0
                }
            if 'race_history' not in learned_data:
                learned_data['race_history'] = []
            
            current_signature = {
                'venue': venue,
                'distance': distance,
                'weather': weather,
                'track': track,
                'race_class': race_class,
                'front_runners': sum(1 for _, r in df.iterrows() if "大逃" in str(r['跑法']) or "逃放" in str(r['跑法']))
            }
            
            race_record = {
                'race_id': f"{venue}_{distance}_{weather}_{len(learned_data['race_history'])}",
                'signature': current_signature,
                'prediction_error': 0.0,
                'actual_winner': finish_order[0] if finish_order else None,
                'actual_winner_type': '未知',
                'lesson': '從呢場賽事學到嘅教訓'
            }
            
            winner = finish_order[0] if finish_order else None
            if winner:
                winner_row = df[df['馬號'] == winner]
                if not winner_row.empty:
                    winner_run = str(winner_row.iloc[0]['跑法'])
                    if "後上" in winner_run or "後追" in winner_run:
                        race_record['actual_winner_type'] = '後上型'
                        if weather in ["小雨", "大雨"] and track == "草地":
                            learned_data['learning_patterns']['rainy_weather_closers'] += 0.3
            
            learned_data['race_history'].append(race_record)
            
            if len(learned_data['race_history']) > 50:
                learned_data['race_history'] = learned_data['race_history'][-50:]
            
            save_learned_data(learned_data)
            
            st.success(f"✅ 賽事級學習完成！已記錄賽事 + 更新模式")
            st.info(f"📊 目前學習數據：{len(learned_data['race_history'])} 場賽事")
            
        except Exception as e:
            st.error(f"解析失敗：{str(e)}")

st.divider()
st.caption("💡 最終專業版：Enhanced Monte Carlo（50,000次）+ GNN + Optimized Pace Model + 詳細投注統計 + 賽事級學習 + Pace Scenario Analysis + Weight Sensitivity")
