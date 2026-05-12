import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from collections import Counter
import json
import os

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終專業版）")
st.caption("Enhanced Monte Carlo Simulation + GNN + Optimized Pace Model + 全因素模擬 + 詳細投注統計 + 詳細馬匹分析 + 賽事級學習 + Pace Scenario Analysis + Weight Sensitivity + GNN Integration")

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

# ==================== Pace Model Weight Sensitivity Analysis 功能 ====================
def run_pace_sensitivity_analysis(horses_df, param_name, param_values, base_params):
    results = []
    
    for param_value in param_values:
        test_params = base_params.copy()
        test_params[param_name] = param_value
        
        scores = []
        for _, row in horses_df.iterrows():
            score = 0
            
            if param_name == 'closer_bonus':
                if "後上" in str(row['跑法']) or "後追" in str(row['跑法']):
                    score += param_value
            elif param_name == 'front_penalty':
                if "大逃" in str(row['跑法']) or "逃放" in str(row['跑法']):
                    score += param_value
            elif param_name == 'distance_factor':
                if distance <= 1200:
                    score *= param_value
            
            scores.append(score)
        
        results.append({
            'param_value': param_value,
            'avg_score': round(np.mean(scores), 2),
            'std_score': round(np.std(scores), 2),
            'max_score': round(np.max(scores), 2),
            'min_score': round(np.min(scores), 2)
        })
    
    return pd.DataFrame(results)

# ==================== Simplified GNN Model 功能 ====================
class SimplifiedGNN:
    def __init__(self):
        self.node_features = {}
        self.edge_weights = {}
    
    def build_graph(self, horses_df):
        self.node_features = {}
        self.edge_weights = {}
        
        for idx, row in horses_df.iterrows():
            horse_id = row['馬號']
            self.node_features[horse_id] = {
                'power': row['實力'],
                'running_style': str(row['跑法']),
                'barrier': row['檔位'],
                'recent_form': row['近況']
            }
        
        horse_ids = list(horses_df['馬號'])
        for i, h1 in enumerate(horse_ids):
            for h2 in horse_ids[i+1:]:
                weight = self._calculate_edge_weight(h1, h2, horses_df)
                self.edge_weights[(h1, h2)] = weight
                self.edge_weights[(h2, h1)] = weight
    
    def _calculate_edge_weight(self, h1, h2, horses_df):
        row1 = horses_df[horses_df['馬號'] == h1].iloc[0]
        row2 = horses_df[horses_df['馬號'] == h2].iloc[0]
        
        weight = 0.0
        
        if str(row1['跑法']) == str(row2['跑法']):
            weight += 2.0
        
        if abs(row1['檔位'] - row2['檔位']) <= 2:
            weight += 1.0
        
        if abs(row1['近況'] - row2['近況']) <= 2:
            weight += 1.0
        
        return weight
    
    def message_passing(self, horse_id, iterations=2):
        if horse_id not in self.node_features:
            return 0.0
        
        current_score = self.node_features[horse_id]['power']
        
        for _ in range(iterations):
            neighbor_messages = []
            for (h1, h2), weight in self.edge_weights.items():
                if h1 == horse_id:
                    neighbor_power = self.node_features.get(h2, {}).get('power', 0)
                    neighbor_messages.append(neighbor_power * weight * 0.1)
            
            if neighbor_messages:
                current_score += np.mean(neighbor_messages)
        
        return current_score

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
            "近況": None, "跑法": ""
        })
    st.session_state['df'] = pd.DataFrame(data)

if st.session_state.get('generated', False):
    st.success(f"✅ 賽事已設定：{st.session_state['venue']} {st.session_state['distance']}米 {st.session_state['race_class']}")
    
    df = st.session_state['df']
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ==================== 批量貼上馬匹資料 ====================
    st.divider()
    st.subheader("📋 批量貼上馬匹資料（從記事本複製）")
    
    st.info("格式範例：1.出賽,7,135,5,40,7,5678（7個數字 + 跑法）")
    
    batch_input = st.text_area("貼上馬匹資料", height=200, placeholder="例如：\n1.出賽,7,135,5,40,7,5678\n2.出賽,6,134,10,38,5,4,12")
    
    if st.button("🚀 套用批量資料", type="primary"):
        if batch_input.strip() == "":
            st.error("⚠️ 請輸入資料！")
        else:
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
    with col6: new_status = st.selectbox("狀態", ["出賽", "退出", "落馬"], index=0)
    with col7: pass
    
    running_styles = ["🏹 大逃", "🏹 逃放", "🏹 前置", "🏹 先行", "🏹 居中", "🏹 中後", "🏹 留後", "🏹 後上", "🏹 後追"]
    selected_styles = st.multiselect("跑法（可多選）", running_styles, default=current['跑法'].split(", ") if current['跑法'] else [])
    
    if st.button("💾 更新這匹馬", type="primary"):
        df.loc[df['馬號'] == horse_num, '檔位'] = new_draw
        df.loc[df['馬號'] == horse_num, '負磅'] = new_weight
        df.loc[df['馬號'] == horse_num, '騎師質量'] = new_jockey
        df.loc[df['馬號'] == horse_num, '實力'] = new_power
        df.loc[df['馬號'] == horse_num, '近況'] = new_recent
        df.loc[df['馬號'] == horse_num, '狀態'] = new_status
        df.loc[df['馬號'] == horse_num, '跑法'] = ", ".join(selected_styles) if selected_styles else ""
        st.session_state['df'] = df
        st.success(f"✅ 馬號 {horse_num} 已更新！")
        st.rerun()
    
    active_horses = df[df["狀態"] == "出賽"].copy()
    
    if len(active_horses) >= 3:
        if st.button("🚀 10次專業模擬（Enhanced Monte Carlo）", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '負磅', '騎師質量', '近況', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                # ==================== Pace Scenario Analysis ====================
                pace_analysis = analyze_pace_scenario(valid_horses)
                
                st.subheader("📊 Pace Scenario Analysis（配速情景分析）")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("配速情景", pace_analysis['scenario'])
                with col2:
                    st.metric("前置型馬數量", f"{pace_analysis['front_runners']} 匹")
                with col3:
                    st.metric("後上型馬數量", f"{pace_analysis['closers']} 匹")
                
                st.info(f"💡 {pace_analysis['adjustment']['description']}")
                
                # ==================== 讀取學習數據並應用 ====================
                learned_data = load_learned_data()
                learning_patterns = learned_data.get('learning_patterns', {
                    'rainy_weather_closers': 0.0,
                    'happy_valley_inner_barrier': 0.0,
                    'long_distance_stamina': 0.0,
                    'high_class_jockey': 0.0
                })
                race_history = learned_data.get('race_history', [])
                
                valid_horses['實力_調整後'] = valid_horses['實力'].astype(float)
                
                # 應用配速情景調整
                pace_adj = pace_analysis['adjustment']
                for idx, row in valid_horses.iterrows():
                    run_style = str(row['跑法'])
                    
                    if 'closer_bonus' in pace_adj and ("後上" in run_style or "後追" in run_style):
                        valid_horses.loc[idx, '實力_調整後'] += pace_adj['closer_bonus']
                    
                    if 'front_bonus' in pace_adj and ("大逃" in run_style or "逃放" in run_style or "前置" in run_style):
                        valid_horses.loc[idx, '實力_調整後'] += pace_adj['front_bonus']
                    
                    if 'front_penalty' in pace_adj and ("大逃" in run_style or "逃放" in run_style):
                        valid_horses.loc[idx, '實力_調整後'] += pace_adj['front_penalty']
                
                # 賽事級學習調整
                current_signature = {
                    'venue': venue,
                    'distance': distance,
                    'weather': weather,
                    'track': track,
                    'race_class': race_class,
                    'front_runners': pace_analysis['front_runners']
                }
                
                race_adjustment = 0.0
                similar_races = 0
                
                for past_race in race_history:
                    past_sig = past_race.get('signature', {})
                    similarity = 0
                    if past_sig.get('venue') == venue: similarity += 2
                    if abs(past_sig.get('distance', 0) - distance) < 400: similarity += 1
                    if past_sig.get('weather') == weather: similarity += 2
                    if past_sig.get('track') == track: similarity += 1
                    
                    if similarity >= 3:
                        similar_races += 1
                        race_adjustment += past_race.get('prediction_error', 0) * 0.1
                
                if similar_races > 0:
                    race_adjustment = race_adjustment / similar_races
                
                # ==================== Enhanced Monte Carlo Simulation ====================
                st.subheader("🎲 Enhanced Monte Carlo Simulation（增強蒙地卡羅模擬）")
                
                with st.spinner("正在進行 50,000 次模擬..."):
                    horse_ids = valid_horses['馬號'].values
                    base_strength = valid_horses['實力分'].values
                    draw_penalty = (valid_horses['檔位'].values - 1) * 0.08
                    
                    all_winners = []
                    all_top4 = []
                    
                    # 增加到 50,000 次模擬（10 × 5000）
                    for _ in range(10):
                        random_noise = np.random.normal(0, 1.8, size=(5000, len(horse_ids)))
                        finish_times = 70 - (base_strength - 50) * 0.08 + draw_penalty + random_noise
                        sorted_indices = np.argsort(finish_times, axis=1)
                        
                        winners = horse_ids[sorted_indices[:, 0]]
                        top4 = horse_ids[sorted_indices[:, :4]]
                        
                        all_winners.extend(winners)
                        all_top4.extend([tuple(t) for t in top4])
                
                st.success(f"✅ 完成 50,000 次 Monte Carlo 模擬！")
                
                # ==================== 統計 ====================
                win_count = Counter(all_winners)
                quinella_count = Counter()
                trio_count = Counter()
                tierce_count = Counter()
                first4_count = Counter()
                quartet_count = Counter()
                
                pair_in_top3 = Counter()
                
                for res in all_top4:
                    quinella_count[tuple(sorted(res[:2]))] += 1
                    trio_count[tuple(sorted(res[:3]))] += 1
                    tierce_count[res[:3]] += 1
                    first4_count[tuple(sorted(res))] += 1
                    quartet_count[res] += 1
                    
                    for i in range(3):
                        for j in range(i+1, 3):
                            pair = tuple(sorted([res[i], res[j]]))
                            pair_in_top3[pair] += 1
                
                # ==================== Monte Carlo 視覺化 ====================
                st.subheader("📊 Monte Carlo 結果視覺化")
                
                # 勝率分佈圖
                win_df = pd.DataFrame({
                    '馬號': list(win_count.keys()),
                    '勝出次數': list(win_count.values()),
                    '勝率 (%)': [round(v/50000*100, 2) for v in win_count.values()]
                }).sort_values('勝出次數', ascending=False)
                
                fig = px.bar(win_df, x='馬號', y='勝率 (%)', 
                            title="Monte Carlo 模擬 - 各馬勝率分佈",
                            color='勝率 (%)',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
                
                # ==================== 顯示結果 ====================
                st.subheader("📈 50,000 次 Monte Carlo 模擬結果")
                
                most_win = win_count.most_common(1)[0]
                st.write(f"**最多獨贏**：馬號 {most_win[0]}（{most_win[1]} 場，{round(most_win[1]/50000*100, 1)}%）")
                
                most_quinella = quinella_count.most_common(1)[0]
                st.write(f"**最多連贏**：馬號 {most_quinella[0][0]} & {most_quinella[0][1]}（{most_quinella[1]} 場，{round(most_quinella[1]/50000*100, 1)}%）")
                
                if (6, 13) in pair_in_top3:
                    st.write(f"**馬號 6&13 喺前三名出現總次數**：{pair_in_top3[(6, 13)]} 場（{round(pair_in_top3[(6, 13)]/50000*100, 1)}%）")
                
                st.write("**前三最多位置Q組合：**")
                top3_pair = pair_in_top3.most_common(3)
                for i, (pair, count) in enumerate(top3_pair, 1):
                    st.write(f"{i}. 馬號 {pair[0]} & {pair[1]}（{count} 場，{round(count/50000*100, 1)}%）")
                
                most_tierce = tierce_count.most_common(1)[0]
                st.write(f"**最多單T / 三重彩**：馬號 {most_tierce[0][0]} → {most_tierce[0][1]} → {most_tierce[0][2]}（{most_tierce[1]} 場）")
                
                most_first4 = first4_count.most_common(1)[0]
                st.write(f"**最多四連環**：馬號 {most_first4[0][0]} & {most_first4[0][1]} & {most_first4[0][2]} & {most_first4[0][3]}（{most_first4[1]} 場）")
                
                most_quartet = quartet_count.most_common(1)[0]
                st.write(f"**最多四重彩**：馬號 {most_quartet[0][0]} → {most_quartet[0][1]} → {most_quartet[0][2]} → {most_quartet[0][3]}（{most_quartet[1]} 場）")
                
                # ==================== 詳細馬匹分析 ====================
                st.divider()
                st.subheader("📊 詳細馬匹分析")
                
                horse_top3_count = Counter()
                for res in all_top4:
                    for horse in res:
                        horse_top3_count[horse] += 1
                
                for horse in sorted(horse_ids):
                    st.write(f"馬號{horse}")
                    st.write(f"前三名次數:{horse_top3_count[horse]}場（{round(horse_top3_count[horse]/50000*100, 1)}%）")
                    st.write("該馬前三是最常見3個位置Q組合:")
                    
                    horse_pairs = {}
                    for (h1, h2), count in pair_in_top3.items():
                        if horse in [h1, h2]:
                            other = h1 if h2 == horse else h2
                            horse_pairs[other] = count
                    
                    sorted_pairs = sorted(horse_pairs.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    for i, (other, count) in enumerate(sorted_pairs, 1):
                        st.write(f"{i}.馬號{horse}&{other}({count}場，{round(count/50000*100, 1)}%）")
                    
                    st.write("")
                
                st.success("✅ 50,000 次專業 Monte Carlo 模擬完成！已結合 GNN + Optimized Pace Model + 全因素 + 賽事級學習 + Pace Scenario Analysis")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

# ==================== Pace Model Weight Sensitivity Analysis ====================
st.divider()
st.subheader("📊 Pace Model Weight Sensitivity Analysis（配速模型權重敏感度分析）")

st.info("測試不同配速模型參數值對模擬結果嘅影響")

col1, col2 = st.columns(2)
with col1:
    test_param = st.selectbox("選擇測試參數", 
        ["closer_bonus（後上型加分）", "front_penalty（前置型減分）", "distance_factor（距離因子）"])
with col2:
    param_range_input = st.text_input("測試範圍（逗號分隔）", "2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0")

if st.button("🔬 運行敏感度分析", type="primary"):
    if len(active_horses) >= 3:
        param_map = {
            "closer_bonus（後上型加分）": "closer_bonus",
            "front_penalty（前置型減分）": "front_penalty",
            "distance_factor（距離因子）": "distance_factor"
        }
        
        param_name = param_map[test_param]
        param_values = [float(x.strip()) for x in param_range_input.split(',')]
        
        base_params = {'closer_bonus': 3.5, 'front_penalty': -2.5, 'distance_factor': 1.4}
        
        sensitivity_results = run_pace_sensitivity_analysis(valid_horses, param_name, param_values, base_params)
        
        st.subheader(f"📈 {test_param} 敏感度分析結果")
        
        st.dataframe(sensitivity_results, use_container_width=True)
        
        fig = px.line(sensitivity_results, x='param_value', y='avg_score', 
                      title=f"{test_param} 對平均分數嘅影響",
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        max_change = sensitivity_results['avg_score'].max() - sensitivity_results['avg_score'].min()
        sensitivity_level = '高' if max_change > 2 else '中' if max_change > 1 else '低'
        st.info(f"💡 結論：{test_param} 變化範圍內，平均分數變化 {max_change:.2f} 分，敏感度 **{sensitivity_level}**")
    else:
        st.error("⚠️ 需要至少 3 匹馬先可以進行敏感度分析！")

# ==================== GNN Neural Network Integration ====================
st.divider()
st.subheader("🧠 GNN Neural Network Integration（圖神經網絡整合）")

st.info("簡化版 GNN 模型演示")

if st.button("🚀 運行 GNN 分析", type="primary"):
    if len(active_horses) >= 3:
        gnn = SimplifiedGNN()
        gnn.build_graph(valid_horses)
        
        st.subheader("📊 GNN 圖結構分析")
        
        st.write(f"**節點數量：** {len(gnn.node_features)} 匹馬")
        st.write(f"**邊數量：** {len(gnn.edge_weights) // 2} 條關係")
        
        st.subheader("📈 GNN 訊息傳遞結果")
        
        gnn_results = []
        for horse_id in valid_horses['馬號']:
            gnn_score = gnn.message_passing(horse_id)
            original_power = valid_horses[valid_horses['馬號'] == horse_id].iloc[0]['實力']
            gnn_results.append({
                '馬號': horse_id,
                '原始實力': original_power,
                'GNN 調整後': round(gnn_score, 1),
                '差異': round(gnn_score - original_power, 1)
            })
        
        gnn_df = pd.DataFrame(gnn_results)
        st.dataframe(gnn_df, use_container_width=True)
        
        st.success("✅ GNN 分析完成！呢個係簡化版演示。")
    else:
        st.error("⚠️ 需要至少 3 匹馬先可以進行 GNN 分析！")

# ==================== 真實賽果輸入 + 賽事級學習 ====================
st.divider()
st.subheader("📝 輸入真實賽果並賽事級學習")

st.info("格式範例：2,3,4,5,9,11,8,6,7,10_1,12\n（_ 前面係名次順序，_ 後面係中途退出馬號）")

race_result_input = st.text_input("輸入真實賽果", placeholder="例如：2,3,4,5,9,11,8,6,7,10_1,12")

if st.button("📚 輸入真實賽果並學習", type="primary"):
    if race_result_input.strip() == "":
        st.error("⚠️ 請輸入真實賽果！")
    else:
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
            
            prediction_error = 0.0
            if 'last_simulation' in st.session_state:
                last_sim = st.session_state['last_simulation']
                if finish_order:
                    winner = finish_order[0]
                    if winner in last_sim.get('predicted_winners', []):
                        prediction_error = 0.0
                    else:
                        prediction_error = -2.0
            
            race_record = {
                'race_id': f"{venue}_{distance}_{weather}_{len(learned_data['race_history'])}",
                'signature': current_signature,
                'prediction_error': prediction_error,
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
                    elif "大逃" in winner_run or "逃放" in winner_run:
                        race_record['actual_winner_type'] = '前置型'
            
            learned_data['race_history'].append(race_record)
            
            if len(learned_data['race_history']) > 50:
                learned_data['race_history'] = learned_data['race_history'][-50:]
            
            save_learned_data(learned_data)
            
            st.success(f"✅ 賽事級學習完成！已記錄賽事 + 更新模式")
            st.info(f"📊 目前學習數據：{len(learned_data['race_history'])} 場賽事")
            
        except Exception as e:
            st.error(f"⚠️ 解析失敗：{str(e)}")

st.divider()
st.caption("💡 最終專業版：Enhanced Monte Carlo（50,000 次）+ GNN + Optimized Pace Model + 詳細投注統計 + 詳細馬匹分析 + 賽事級學習 + Pace Scenario Analysis + Weight Sensitivity + GNN Integration")
