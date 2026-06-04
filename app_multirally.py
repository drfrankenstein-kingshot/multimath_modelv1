import streamlit as st
import numpy as np
import copy
from simulator_engine import kingshot_multirally_sim2, TroopSide, load_hero_db

# =========================================================================
# --- SECURITY GATEWAY ---
# =========================================================================
SECRET_PASSCODE = "Frank_BattleSimulator"

st.set_page_config(page_title="Kingshot Multi-Rally Simulator", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Security Access Required")
    user_input = st.text_input("Enter Alliance Passcode:", type="password")
    
    if st.button("Unlock Simulator"):
        if user_input == SECRET_PASSCODE:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid passcode. Access denied.")
else:
    # =========================================================================
    # --- SIMULATOR APPLICATION (UNLOCKED) ---
    # =========================================================================
    st.title("⚔️ Kingshot Multi-Rally Tactical Engine")
    st.caption("Simulate sequential multi-rally Waves with granular composition validation.")
    
    if st.sidebar.button("Lock Application"):
        st.session_state["authenticated"] = False
        st.rerun()

    hero_db = load_hero_db()
    
    # Define locked hero options containing "None" at the first index (0)
    hero_list = ["None"] + sorted(list(hero_db.keys()))
# Master tracking lists updated with custom variants and Gen 4 targets
    infantry_heroes = ["None"] + sorted(["Eric", "Zoe", "Amadeus", "Helga", "Howard", "Alcar"])
    cavalry_heroes = ["None"] + sorted(["Gordon", "Fahd", "Chenko", "Petra", "Hilde", "Jabel", "Margot"])
    archer_heroes = ["None"] + sorted(["Jaegar", "Marlin", "Saul", "Yaenwoo", "Amane", "Quinn", "Rosa"])

    # Layout Split: Main Screen for Waves, Sidebar for the Target Garrison
    col_main, col_side = st.columns([2, 1])
    
    # -------------------------------------------------------------------------
    # --- SIDEBAR / RIGHT COLUMN: GARRISON TARGET CONFIG ---
    # -------------------------------------------------------------------------
    with col_side:
        st.header("Garrison Setup")
        
        st.markdown("**Garrison Base Troop Level**")
        gc1, gc2 = st.columns(2)
        g_tier = gc1.selectbox("Garrison Troop Tier", range(1, 12), index=10, key="gtier") 
        g_tg = gc2.selectbox("Garrison Troop TG Level", range(0, 6), index=5, key="gtg")       
        st.markdown("---")
        
        g_input_style = st.radio("Garrison Troop Input Style", ("Raw Counts", "Capacity + Ratios"), key="g_style")
        
        if g_input_style == "Raw Counts":
            g_inf = st.number_input("Garrison Infantry Count", value=1500000)
            g_cav = st.number_input("Garrison Cavalry Count", value=500000)
            g_arc = st.number_input("Garrison Archer Count", value=800000)
            g_total_troops = g_inf + g_cav + g_arc
            g_valid = True
        else:
            g_total_troops = st.number_input("Total Garrison Capacity Target", value=2800000, step=100000)
            st.markdown("**Adjust Garrison Ratios (Must equal 100%)**")
            
            g_df = [{"Class": "Infantry", "Ratio %": 50}, 
                    {"Class": "Cavalry", "Ratio %": 20}, 
                    {"Class": "Archer", "Ratio %": 30}]
            
            edited_g_df = st.data_editor(
                g_df,
                column_config={
                    "Class": st.column_config.TextColumn("Troop Class", disabled=True),
                    "Ratio %": st.column_config.NumberColumn("Ratio %", min_value=0, max_value=100, step=1, format="%d%%")
                },
                disabled=["Class"],
                hide_index=True,
                key="g_ratio_editor"
            )
            
            g_total_pct = sum(row["Ratio %"] for row in edited_g_df)
            if g_total_pct != 100:
                st.error(f"❌ Garrison ratios sum to **{g_total_pct}%**. Adjust until it equals exactly 100%.")
                g_valid = False
            else:
                g_valid = True
            
            g_inf = int(g_total_troops * (edited_g_df[0]["Ratio %"] / 100.0))
            g_cav = int(g_total_troops * (edited_g_df[1]["Ratio %"] / 100.0))
            g_arc = int(g_total_troops * (edited_g_df[2]["Ratio %"] / 100.0))
        
        with st.expander("🎖️ Garrison Leadership & Widgets"):
            st.markdown("### Main Leaders (3)")
            hc1, wc1 = st.columns([3, 1])
            g_lead1 = hc1.selectbox("Infantry Hero", infantry_heroes, index=infantry_heroes.index("Amadeus") if "Amadeus" in infantry_heroes else 0, key="gl1")
            g_wid1 = wc1.number_input("Widget 1", 0, 10, 10, key="gw1")
            
            hc2, wc2 = st.columns([3, 1])
            g_lead2 = hc2.selectbox("Cavalry Hero", cavalry_heroes, index=cavalry_heroes.index("Hilde") if "Hilde" in cavalry_heroes else 0, key="gl2")
            g_wid2 = wc2.number_input("Widget 2", 0, 10, 10, key="gw2")
            
            hc3, wc3 = st.columns([3, 1])
            g_lead3 = hc3.selectbox("Archer Hero", archer_heroes, index=archer_heroes.index("Marlin") if "Marlin" in archer_heroes else 0, key="gl3")
            g_wid3 = wc3.number_input("Widget 3", 0, 10, 10, key="gw3")
            
            st.markdown("---")
            st.markdown("### Joiner/Supporter Heroes (4)")
            g_sup1 = st.selectbox("Supporter 1", hero_list, index=0, key="gs1")
            g_sup2 = st.selectbox("Supporter 2", hero_list, index=0, key="gs2")
            g_sup3 = st.selectbox("Supporter 3", hero_list, index=0, key="gs3")
            g_sup4 = st.selectbox("Supporter 4", hero_list, index=0, key="gs4")
            
        with st.expander("📊 Target Garrison Combat Stats"):
            g_inf_atk = st.number_input("Inf Attack %", value=850.0, key="gia")
            g_inf_def = st.number_input("Inf Defense %", value=900.0, key="gid")
            g_inf_let = st.number_input("Inf Lethality %", value=1100.0, key="gil")
            g_inf_hp  = st.number_input("Inf Health %", value=1100.0, key="gih")
            st.markdown("---")
            g_cav_atk = st.number_input("Cav Attack %", value=800.0, key="gca")
            g_cav_def = st.number_input("Cav Defense %", value=800.0, key="gcd")
            g_cav_let = st.number_input("Cav Lethality %", value=1000.0, key="gcl")
            g_cav_hp  = st.number_input("Cav Health %", value=1000.0, key="gch")
            st.markdown("---")
            g_arc_atk = st.number_input("Arc Attack %", value=850.0, key="gaa")
            g_arc_def = st.number_input("Arc Defense %", value=800.0, key="gad")
            g_arc_let = st.number_input("Arc Lethality %", value=1100.0, key="gal")
            g_arc_hp  = st.number_input("Arc Health %", value=1000.0, key="gah")

    # -------------------------------------------------------------------------
    # --- MAIN COLUMN: DYNAMIC ATTACKING RALLY WAVES ---
    # -------------------------------------------------------------------------
    with col_main:
        st.header(" Attacking Rally Waves Configuration")
        
        num_waves = st.number_input("Number of Rally Waves", min_value=1, max_value=5, value=2, step=1)
        wave_tabs = st.tabs([f"🌊 Wave {i+1}" for i in range(num_waves)])
        
        wave_configs = {}
        
        for i, tab in enumerate(wave_tabs):
            with tab:
                st.subheader(f"Parameters for Rally Wave #{i+1}")
                
                w_col1, w_col2 = st.columns(2)
                
                with w_col1:
                    st.markdown("**Wave Base Troop Level**")
                    wc1, wc2 = st.columns(2)
                    w_tier = wc1.selectbox(f"Wave {i+1} Troop Tier", range(1, 12), index=9, key=f"wtier_{i}") 
                    w_tg = wc2.selectbox(f"Wave {i+1} Troop TG Level", range(0, 6), index=5, key=f"wtg_{i}")       
                    st.markdown("---")
                    
                    w_input_style = st.radio(f"Wave {i+1} Troop Input Style", ("Raw Counts", "Rally Size + Ratios"), key=f"w_style_{i}")
                    if w_input_style == "Raw Counts":
                        a_inf = st.number_input("Infantry Count", value=600000, key=f"w_inf_{i}")
                        a_cav = st.number_input("Cavalry Count", value=200000, key=f"w_cav_{i}")
                        a_arc = st.number_input("Archer Count", value=200000, key=f"w_arc_{i}")
                        st.session_state[f"w_valid_{i}"] = True
                    else:
                        a_total_capacity = st.number_input("Rally Size Capacity Limit", value=1000000, step=50000, key=f"w_cap_{i}")
                        st.markdown(f"**Adjust Wave {i+1} Ratios (Must equal 100%)**")
                        
                        w_df = [{"Class": "Infantry", "Ratio %": 60}, 
                                {"Class": "Cavalry", "Ratio %": 20}, 
                                {"Class": "Archer", "Ratio %": 20}]
                        
                        edited_w_df = st.data_editor(
                            w_df,
                            column_config={
                                "Class": st.column_config.TextColumn("Troop Class", disabled=True),
                                "Ratio %": st.column_config.NumberColumn("Ratio %", min_value=0, max_value=100, step=1, format="%d%%")
                            },
                            disabled=["Class"],
                            hide_index=True,
                            key=f"w_ratio_editor_{i}"
                        )
                        
                        w_total_pct = sum(row["Ratio %"] for row in edited_w_df)
                        if w_total_pct != 100:
                            st.error(f"❌ Wave {i+1} ratios sum to **{w_total_pct}%**. Adjust until it equals exactly 100%.")
                            st.session_state[f"w_valid_{i}"] = False
                        else:
                            st.session_state[f"w_valid_{i}"] = True
                        
                        a_inf = int(a_total_capacity * (edited_w_df[0]["Ratio %"] / 100.0))
                        a_cav = int(a_total_capacity * (edited_w_df[1]["Ratio %"] / 100.0))
                        a_arc = int(a_total_capacity * (edited_w_df[2]["Ratio %"] / 100.0))
                    
                with w_col2:
                    st.markdown("**Main Leaders & Widgets**")
                    ahc1, awc1 = st.columns([3, 1])
                    a_l1 = ahc1.selectbox("Infantry Hero", infantry_heroes, index=0, key=f"wl1_{i}")
                    a_w1 = awc1.number_input("Widget 1", 0, 10, 10, key=f"ww1_{i}")
                    
                    ahc2, awc2 = st.columns([3, 1])
                    a_l2 = ahc2.selectbox("Cavalry Hero", cavalry_heroes, index=0, key=f"wl2_{i}")
                    a_w2 = awc2.number_input("Widget 2", 0, 10, 10, key=f"ww2_{i}")
                    
                    ahc3, awc3 = st.columns([3, 1])
                    a_l3 = ahc3.selectbox("Archer Hero", archer_heroes, index=0, key=f"wl3_{i}")
                    a_w3 = awc3.number_input("Widget 3", 0, 10, 10, key=f"ww3_{i}")
                    
                    st.markdown("---")
                    st.markdown("**Joiner/Supporter Heroes (4)**")
                    a_s1 = st.selectbox("Supporter 1", hero_list, index=0, key=f"ws1_{i}")
                    a_s2 = st.selectbox("Supporter 2", hero_list, index=0, key=f"ws2_{i}")
                    a_s3 = st.selectbox("Supporter 3", hero_list, index=0, key=f"ws3_{i}")
                    a_s4 = st.selectbox("Supporter 4", hero_list, index=0, key=f"ws4_{i}")
                
                with st.expander(f"📊 Wave {i+1} Core Combat Stats Override"):
                    sc1, sc2, sc3 = st.columns(3)
                    
                    with sc1:
                        st.markdown("**Infantry Stats**")
                        a_inf_atk = st.number_input("Inf Atk %", value=1000.0, key=f"a_ia_{i}")
                        a_inf_def = st.number_input("Inf Def %", value=800.0, key=f"a_id_{i}")
                        a_inf_let = st.number_input("Inf Let %", value=1100.0, key=f"a_il_{i}")
                        a_inf_hp  = st.number_input("Inf HP %", value=900.0, key=f"a_ih_{i}")
                        
                    with sc2:
                        st.markdown("**Cavalry Stats**")
                        a_cav_atk = st.number_input("Cav Atk %", value=900.0, key=f"a_ca_{i}")
                        a_cav_def = st.number_input("Cav Def %", value=750.0, key=f"a_cd_{i}")
                        a_cav_let = st.number_input("Cav Let %", value=850.0, key=f"a_cl_{i}")
                        a_cav_hp  = st.number_input("Cav HP %", value=700.0, key=f"a_ch_{i}")
                        
                    with sc3:
                        st.markdown("**Archer Stats**")
                        a_arc_atk = st.number_input("Arc Atk %", value=900.0, key=f"a_aa_{i}")
                        a_arc_def = st.number_input("Arc Def %", value=700.0, key=f"a_ad_{i}")
                        a_arc_let = st.number_input("Arc Let %", value=1050.0, key=f"a_al_{i}")
                        a_arc_hp  = st.number_input("Arc HP %", value=800.0, key=f"a_ah_{i}")
                    
                    wave_configs[i] = {
                        "troops": [a_inf, a_cav, a_arc],
                        "tier": w_tier,
                        "tg": w_tg,
                        "leaders": [a_l1, a_l2, a_l3],
                        "supporters": [a_s1, a_s2, a_s3, a_s4],
                        "widgets": [a_w1, a_w2, a_w3, 0, 0, 0, 0],
                        "stats": [
                            [a_inf_atk, a_inf_def, a_inf_let, a_inf_hp],
                            [a_cav_atk, a_cav_def, a_cav_let, a_cav_hp],
                            [a_arc_atk, a_arc_def, a_arc_let, a_arc_hp]
                        ]
                    }

        st.markdown("---")
        num_runs = st.number_input("Monte Carlo Matrix Iterations", min_value=10, max_value=1000, value=200, step=50)

        # Ensure all data grids conform perfectly to 100% bounds prior to rendering execution hooks
        all_waves_valid = all(st.session_state.get(f"w_valid_{w_idx}", True) for w_idx in range(num_waves))
        
        if all_waves_valid and g_valid:
            if st.button("Run Multi-Rally Simulation Sequence"):
                with st.spinner("Processing continuous battlefield math blocks..."):
                    
                    # 1. Parse and build the Target Garrison object
                    garrison_widgets = [g_wid1, g_wid2, g_wid3, 0, 0, 0, 0]
                    
                    g_combat_stats = copy.deepcopy([
                        [g_inf_atk, g_inf_def, g_inf_let, g_inf_hp],
                        [g_cav_atk, g_cav_def, g_cav_let, g_cav_hp],
                        [g_arc_atk, g_arc_def, g_arc_let, g_arc_hp]
                    ])
                    
                    garrison_setup = TroopSide(
                        troops=[g_inf, g_cav, g_arc],
                        stats=g_combat_stats,
                        leader_heroes=[g_lead1, g_lead2, g_lead3],
                        supporter_heroes=[g_sup1, g_sup2, g_sup3, g_sup4],
                        tier=g_tier,          
                        tg_level=g_tg,        
                        widget_levels=garrison_widgets
                    )
                    
                    # 2. Build the array list of attacking wave inputs dynamically
                    rally_waves_input = []
                    for wave_idx in range(num_waves):
                        w_data = wave_configs[wave_idx]
                        w_combat_stats = copy.deepcopy(w_data["stats"])
                            
                        wave_setup = TroopSide(
                            troops=w_data["troops"],
                            stats=w_combat_stats,
                            leader_heroes=w_data["leaders"],
                            supporter_heroes=w_data["supporters"],
                            tier=w_data["tier"],     
                            tg_level=w_data["tg"],   
                            widget_levels=w_data["widgets"]
                        )
                        rally_waves_input.append(wave_setup)

                    # 3. Process tracking arrays over the complete simulation run
                    garrison_survivors_total = 0
                    garrison_breakdown_avg = np.zeros(3)
                    
                    wave_survivor_tracking = {w: 0 for w in range(num_waves)}
                    wave_win_counts = {w: 0 for w in range(num_waves)} 

                    for _ in range(int(num_runs)):
                        temp_garrison = copy.deepcopy(garrison_setup)
                        temp_waves = copy.deepcopy(rally_waves_input)
                        
                        final_garrison, logs = kingshot_multirally_sim2(temp_waves, temp_garrison)
                        
                        garrison_survivors_total += np.sum(final_garrison.troops)
                        garrison_breakdown_avg += final_garrison.troops
                        
                        for step_idx, log in enumerate(logs):
                            att_surv = np.sum(log['attacker_surviving'])
                            wave_survivor_tracking[step_idx] += att_surv
                            
                            if att_surv > 0:
                                wave_win_counts[step_idx] += 1

                    # 4. Generate Averages
                    avg_g_survivors = garrison_survivors_total / num_runs
                    avg_g_breakdown = garrison_breakdown_avg / num_runs

                    # =========================================================================
                    # --- RESULTS DISPLAY ---
                    # =========================================================================
                    st.success("Simulation Sequence Complete!")
                    
                    if avg_g_survivors <= 0:
                        st.markdown("### STATUS: <span style='color:red'>GARRISON COMPLETELY BROKEN</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"### STATUS: <span style='color:green'>GARRISON HELD (Avg. {avg_g_survivors:,.0f} Total Troops Left)</span>", unsafe_allow_html=True)

                    out_col1, out_col2 = st.columns(2)
                    
                    with out_col1:
                        st.markdown("#### Final Defense Status")
                        st.table({
                            "Troop Class": ["Infantry", "Cavalry", "Archers", "Total Remaining"],
                            "Remaining (Avg)": [
                                f"{avg_g_breakdown[0]:,.0f}", 
                                f"{avg_g_breakdown[1]:,.0f}", 
                                f"{avg_g_breakdown[2]:,.0f}",
                                f"{avg_g_survivors:,.0f}" 
                            ]
                        })
                        
                    with out_col2:
                        st.markdown("#### Attacker Wave Performance")
                        wave_perf_display = []
                        for w_idx in range(num_waves):
                            avg_w_surv = wave_survivor_tracking[w_idx] / num_runs
                            win_rate_percent = (wave_win_counts[w_idx] / num_runs) * 100
                            
                            wave_perf_display.append({
                                "Rally Wave": f"Wave #{w_idx + 1}",
                                "T-Level": f"T{wave_configs[w_idx]['tier']} TG{wave_configs[w_idx]['tg']}",
                                "Win Rate %": f"{win_rate_percent:.1f}%", 
                                "Avg Retained Troops": f"{avg_w_surv:,.0f}"
                            })
                        st.table(wave_perf_display)
        else:
            st.button("Run Multi-Rally Simulation Sequence", disabled=True, help="Fix troop configuration ratio errors to execute mathematical blocks.")