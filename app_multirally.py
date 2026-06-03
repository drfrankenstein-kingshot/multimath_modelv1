import streamlit as st
import numpy as np
import copy
from simulator_engine import kingshot_multirally_sim2, TroopSide, load_hero_db

# Helper to calculate widget expedition bonus based on even-level steps
def get_widget_bonus(level):
    if level == 0:
        return 0.0
    even_level = (level // 2) * 2
    return 2.5 + (even_level / 2) * 2.5

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
    st.title("⚔️ Kingshot Multi-Rally Tactical Engine (V2)")
    st.caption("Simulate sequential multi-rally waves crashing against a sustained Garrison setup.")
    
    if st.sidebar.button("Lock Application"):
        st.session_state["authenticated"] = False
        st.rerun()

    hero_list = sorted(list(load_hero_db().keys()))

    # Layout Split: Main Screen for Waves, Sidebar for the Target Garrison
    col_main, col_side = st.columns([2, 1])
    
    # -------------------------------------------------------------------------
    # --- SIDEBAR / RIGHT COLUMN: GARRISON TARGET CONFIG ---
    # -------------------------------------------------------------------------
    with col_side:
        st.header("🏰 Target Garrison Setup")
        g_inf = st.number_input("Garrison Infantry Count", value=1500000)
        g_cav = st.number_input("Garrison Cavalry Count", value=500000)
        g_arc = st.number_input("Garrison Archer Count", value=800000)
        
        st.markdown("**Garrison Purity Ratios (TG3)**")
        g_ratio_inf = st.slider("Garrison Infantry TG3 %", 0.0, 1.0, 1.0)
        g_ratio_cav = st.slider("Garrison Cavalry TG3 %", 0.0, 1.0, 1.0)
        g_ratio_arc = st.slider("Garrison Archer TG3 %", 0.0, 1.0, 1.0)
        
        with st.expander("🎖️ Garrison Leadership & Widgets"):
            st.markdown("### Main Leaders (3)")
            hc1, wc1 = st.columns([3, 1])
            g_lead1 = hc1.selectbox("Garrison Lead 1", hero_list, index=hero_list.index("Amadeus") if "Amadeus" in hero_list else 0, key="gl1")
            g_wid1 = wc1.number_input("Widget 1", 0, 10, 10, key="gw1")
            
            hc2, wc2 = st.columns([3, 1])
            g_lead2 = hc2.selectbox("Garrison Lead 2", hero_list, index=hero_list.index("Hilde") if "Hilde" in hero_list else 0, key="gl2")
            g_wid2 = wc2.number_input("Widget 2", 0, 10, 10, key="gw2")
            
            hc3, wc3 = st.columns([3, 1])
            g_lead3 = hc3.selectbox("Garrison Lead 3", hero_list, index=hero_list.index("Marlin") if "Marlin" in hero_list else 0, key="gl3")
            g_wid3 = wc3.number_input("Widget 3", 0, 10, 10, key="gw3")
            
            st.markdown("---")
            st.markdown("### Joiner/Supporter Heroes (4)")
            g_sup1 = st.selectbox("Supporter 1", hero_list, index=0, key="gs1")
            g_sup2 = st.selectbox("Supporter 2", hero_list, index=0, key="gs2")
            g_sup3 = st.selectbox("Supporter 3", hero_list, index=0, key="gs3")
            g_sup4 = st.selectbox("Supporter 4", hero_list, index=0, key="gs4")
            
        with st.expander("📊 Target Garrison Combat Stats"):
            st.markdown("**Infantry Stats**")
            g_inf_atk = st.number_input("Inf Attack %", value=850.0, key="gia")
            g_inf_def = st.number_input("Inf Defense %", value=900.0, key="gid")
            g_inf_let = st.number_input("Inf Lethality %", value=1100.0, key="gil")
            g_inf_hp  = st.number_input("Inf Health %", value=1100.0, key="gih")
            st.markdown("---")
            st.markdown("**Cavalry Stats**")
            g_cav_atk = st.number_input("Cav Attack %", value=800.0, key="gca")
            g_cav_def = st.number_input("Cav Defense %", value=800.0, key="gcd")
            g_cav_let = st.number_input("Cav Lethality %", value=1000.0, key="gcl")
            g_cav_hp  = st.number_input("Cav Health %", value=1000.0, key="gch")
            st.markdown("---")
            st.markdown("**Archer Stats**")
            g_arc_atk = st.number_input("Arc Attack %", value=850.0, key="gaa")
            g_arc_def = st.number_input("Arc Defense %", value=800.0, key="gad")
            g_arc_let = st.number_input("Arc Lethality %", value=1100.0, key="gal")
            g_arc_hp  = st.number_input("Arc Health %", value=1000.0, key="gah")

    # -------------------------------------------------------------------------
    # --- MAIN COLUMN: DYNAMIC ATTACKING RALLY WAVES ---
    # -------------------------------------------------------------------------
    with col_main:
        st.header("🚀 Attacking Rally Waves Configuration")
        
        # Select the total number of consecutive rallies hitting this target
        num_waves = st.number_input("Number of Rally Waves", min_value=1, max_value=5, value=2, step=1)
        
        # Create tabs dynamically based on the number of waves selected
        wave_tabs = st.tabs([f"🌊 Wave {i+1}" for i in range(num_waves)])
        
        # Dictionary containers to store UI inputs dynamically per wave
        wave_configs = {}
        
        for i, tab in enumerate(wave_tabs):
            with tab:
                st.subheader(f"Parameters for Rally Wave #{i+1}")
                
                w_col1, w_col2 = st.columns(2)
                
                with w_col1:
                    st.markdown("**Troop Configuration**")
                    a_inf = st.number_input("Infantry Count", value=600000, key=f"w_inf_{i}")
                    a_cav = st.number_input("Cavalry Count", value=200000, key=f"w_cav_{i}")
                    a_arc = st.number_input("Archer Count", value=200000, key=f"w_arc_{i}")
                    
                    st.markdown("**TG3 Purity**")
                    a_r_inf = st.slider("Inf TG3 %", 0.0, 1.0, 1.0, key=f"w_rinf_{i}")
                    a_r_cav = st.slider("Cav TG3 %", 0.0, 1.0, 1.0, key=f"w_rcav_{i}")
                    a_r_arc = st.slider("Arc TG3 %", 0.0, 1.0, 1.0, key=f"w_rarc_{i}")
                    
                with w_col2:
                    st.markdown("**Main Leaders (3)**")
                    ahc1, awc1 = st.columns([3, 1])
                    a_l1 = ahc1.selectbox("Rally Leader 1", hero_list, index=0, key=f"wl1_{i}")
                    a_w1 = awc1.number_input("Widget 1", 0, 10, 10, key=f"ww1_{i}")
                    
                    ahc2, awc2 = st.columns([3, 1])
                    a_l2 = ahc2.selectbox("Rally Leader 2", hero_list, index=0, key=f"wl2_{i}")
                    a_w2 = awc2.number_input("Widget 2", 0, 10, 10, key=f"ww2_{i}")
                    
                    ahc3, awc3 = st.columns([3, 1])
                    a_l3 = ahc3.selectbox("Rally Leader 3", hero_list, index=0, key=f"wl3_{i}")
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
                        "ratios": [a_r_inf, a_r_cav, a_r_arc],
                        "leaders": [a_l1, a_l2, a_l3],
                        "supporters": [a_s1, a_s2, a_s3, a_s4],
                        "widgets": [a_w1, a_w2, a_w3, 0, 0, 0, 0],  # Hardcoded 0 for the 4 supporter slots
                        "stats": [
                            [a_inf_atk, a_inf_def, a_inf_let, a_inf_hp],
                            [a_cav_atk, a_cav_def, a_cav_let, a_cav_hp],
                            [a_arc_atk, a_arc_def, a_arc_let, a_arc_hp]
                        ]
                    }

        st.markdown("---")
        num_runs = st.number_input("Monte Carlo Matrix Iterations", min_value=10, max_value=1000, value=200, step=50)

        # =========================================================================
        # --- EXECUTION LOOP ---
        # =========================================================================
        if st.button("🚀 Run Multi-Rally Simulation Sequence"):
            with st.spinner("Processing continuous battlefield math blocks..."):
                
                # 1. Parse and build the Target Garrison object
                garrison_widgets = [g_wid1, g_wid2, g_wid3, 0, 0, 0, 0]  # Hardcoded 0 for the 4 supporter slots
                garrison_widget_total = sum(get_widget_bonus(lvl) for lvl in garrison_widgets)
                
                g_combat_stats = copy.deepcopy([
                    [g_inf_atk + garrison_widget_total, g_inf_def + garrison_widget_total, g_inf_let, g_inf_hp],
                    [g_cav_atk + garrison_widget_total, g_cav_def + garrison_widget_total, g_cav_let, g_cav_hp],
                    [g_arc_atk + garrison_widget_total, g_arc_def + garrison_widget_total, g_arc_let, g_arc_hp]
                ])
                
                garrison_setup = TroopSide(
                    troops=[g_inf, g_cav, g_arc],
                    stats=g_combat_stats,
                    leader_heroes=[g_lead1, g_lead2, g_lead3],
                    supporter_heroes=[g_sup1, g_sup2, g_sup3, g_sup4],
                    tg3_ratio=[g_ratio_inf, g_ratio_cav, g_ratio_arc],
                    widget_levels=garrison_widgets
                )
                
                # 2. Build the array list of attacking wave inputs dynamically
                rally_waves_input = []
                for wave_idx in range(num_waves):
                    w_data = wave_configs[wave_idx]
                    
                    wave_widget_total = sum(get_widget_bonus(lvl) for lvl in w_data["widgets"])
                    w_combat_stats = copy.deepcopy(w_data["stats"])
                    
                    for row in range(3):
                        w_combat_stats[row][0] += wave_widget_total
                        w_combat_stats[row][1] += wave_widget_total
                        
                    wave_setup = TroopSide(
                        troops=w_data["troops"],
                        stats=w_combat_stats,
                        leader_heroes=w_data["leaders"],
                        supporter_heroes=w_data["supporters"],
                        tg3_ratio=w_data["ratios"],
                        widget_levels=w_data["widgets"]
                    )
                    rally_waves_input.append(wave_setup)

                # 3. Process tracking arrays over the complete simulation run
                garrison_survivors_total = 0
                garrison_breakdown_avg = np.zeros(3)
                wave_survivor_tracking = {w: 0 for w in range(num_waves)}

                for _ in range(int(num_runs)):
                    temp_garrison = copy.deepcopy(garrison_setup)
                    temp_waves = copy.deepcopy(rally_waves_input)
                    
                    final_garrison, logs = kingshot_multirally_sim2(temp_waves, temp_garrison)
                    
                    garrison_survivors_total += np.sum(final_garrison.troops)
                    garrison_breakdown_avg += final_garrison.troops
                    
                    for step_idx, log in enumerate(logs):
                        wave_survivor_tracking[step_idx] += np.sum(log['attacker_surviving'])

                # 4. Generate Averages
                avg_g_survivors = garrison_survivors_total / num_runs
                avg_g_breakdown = garrison_breakdown_avg / num_runs

                # =========================================================================
                # --- RESULTS DISPLAY ---
                # =========================================================================
                st.success("Simulation Sequence Complete!")
                
                if avg_g_survivors <= 0:
                    st.markdown("### 🏆 STATUS: <span style='color:red'>GARRISON COMPLETELY BROKEN</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"### 🏰 STATUS: <span style='color:green'>GARRISON HELD (Avg. {avg_g_survivors:,.0f} Troops Left)</span>", unsafe_allow_html=True)

                out_col1, out_col2 = st.columns(2)
                
                with out_col1:
                    st.markdown("#### 🛡️ Final Defense Status")
                    st.table({
                        "Troop Class": ["Frontline Infantry", "Flanking Cavalry", "Backend Archers"],
                        "Remaining (Avg)": [f"{avg_g_breakdown[0]:,.0f}", f"{avg_g_breakdown[1]:,.0f}", f"{avg_g_breakdown[2]:,.0f}"]
                    })
                    
                with out_col2:
                    st.markdown("#### 🚀 Attacker Wave Performance")
                    wave_perf_display = []
                    for w_idx in range(num_waves):
                        avg_w_surv = wave_survivor_tracking[w_idx] / num_runs
                        wave_perf_display.append({
                            "Rally Wave": f"Wave #{w_idx + 1}",
                            "Avg Retained Troops": f"{avg_w_surv:,.0f}"
                        })
                    st.table(wave_perf_display)