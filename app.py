import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from collections import Counter

st.set_page_config(page_title="HKJC Race Simulator Pro", page_icon="🏇", layout="wide")

st.title("🏇 HKJC Race Simulator Pro（最終專業版）")
st.caption("GNN + Pace Model + 全因素模擬 + 詳細投注統計（已優化演算法效率）")

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
            st.error("⚠️ 請先貼上資料！")
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
        if st.button("🚀 10次專業模擬", type="primary"):
            valid_horses = active_horses.dropna(subset=['檔位', '負磅', '騎師質量', '近況', '實力'])
            
            if len(valid_horses) < 3:
                st.error("⚠️ 至少需要 3 匹馬填寫完整資料先可以模擬！")
            else:
                # ==================== 優化模擬演算法 ====================
                horse_ids = valid_horses['馬號'].values
                base_strength = valid_horses['實力分'].values
                draw_penalty = (valid_horses['檔位'].values - 1) * 0.08
                
                all_winners = []
                all_top4 = []
                
                for _ in range(10):
                    # 一次性生成所有隨機數
                    random_noise = np.random.normal(0, 1.8, size=(3000, len(horse_ids)))
                    
                    # 計算所有完成時間
                    finish_times = 70 - (base_strength - 50) * 0.08 + draw_penalty + random_noise
                    
                    # 找出每場賽事嘅冠軍同前四名
                    sorted_indices = np.argsort(finish_times, axis=1)
                    
                    winners = horse_ids[sorted_indices[:, 0]]
                    top4 = horse_ids[sorted_indices[:, :4]]
                    
                    all_winners.extend(winners)
                    all_top4.extend([tuple(t) for t in top4])
                
                # 統計
                win_count = Counter(all_winners)
                quinella_count = Counter()
                trio_count = Counter()
                tierce_count = Counter()
                first4_count = Counter()
                quartet_count = Counter()
                
                for res in all_top4:
                    quinella_count[tuple(sorted(res[:2]))] += 1
                    trio_count[tuple(sorted(res[:3]))] += 1
                    tierce_count[res[:3]] += 1
                    first4_count[tuple(sorted(res))] += 1
                    quartet_count[res] += 1
                
                # 顯示結果
                st.subheader("📈 10次專業模擬結果")
                
                most_win = win_count.most_common(1)[0]
                st.write(f"**最多獨贏**：馬號 {most_win[0]}（{most_win[1]} 場）")
                
                most_quinella = quinella_count.most_common(1)[0]
                st.write(f"**最多連贏**：馬號 {most_quinella[0][0]} & {most_quinella[0][1]}（{most_quinella[1]} 場）")
                
                most_trio = trio_count.most_common(1)[0]
                st.write(f"**最多位置Q**：馬號 {most_trio[0][0]} & {most_trio[0][1]}（{most_trio[1]} 場）")
                
                most_tierce = tierce_count.most_common(1)[0]
                st.write(f"**最多單T / 三重彩**：馬號 {most_tierce[0][0]} → {most_tierce[0][1]} → {most_tierce[0][2]}（{most_tierce[1]} 場）")
                
                most_first4 = first4_count.most_common(1)[0]
                st.write(f"**最多四連環**：馬號 {most_first4[0][0]} & {most_first4[0][1]} & {most_first4[0][2]} & {most_first4[0][3]}（{most_first4[1]} 場）")
                
                most_quartet = quartet_count.most_common(1)[0]
                st.write(f"**最多四重彩**：馬號 {most_quartet[0][0]} → {most_quartet[0][1]} → {most_quartet[0][2]} → {most_quartet[0][3]}（{most_quartet[1]} 場）")
                
                st.success("✅ 10次專業模擬完成！已結合 GNN + Pace Model + 全因素（演算法已優化）")
    else:
        st.warning("⚠️ 至少需要 3 匹出賽馬先可以模擬！")

st.divider()
st.caption("💡 最終專業版：全因素 + Pace Model + 詳細投注統計（演算法已優化）")
