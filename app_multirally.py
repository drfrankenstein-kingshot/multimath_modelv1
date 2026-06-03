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
        
        # --- NEW: Unified Garrison Troop Level ---
        st.markdown("**Garrison Base Troop Level**")
        gc1, gc2 = st.columns(2)
        g_tier = gc1.selectbox("Garrison Tier", range(1, 12), index=10, key="gtier") # Default T11
        g_tg = gc2.selectbox("Garrison TG", range(0, 6), index=5, key="gtg")       # Default TG5
        st.markdown("---")
        
        g_inf = st.number_input("Garrison Infantry Count", value=1500000)
        g_cav = st.number_input("Garrison Cavalry Count", value=500000)
        g_arc = st.number_input("Garrison Archer Count", value=800000)
        
        # ... (Garrison Heroes and Stats expanders remain the same) ...

    # -------------------------------------------------------------------------
    # --- MAIN COLUMN: DYNAMIC ATTACKING RALLY WAVES ---
    # -------------------------------------------------------------------------
    with col_main:
        st.header("🚀 Attacking Rally Waves Configuration")
        num_waves = st.number_input("Number of Rally Waves", min_value=1, max_value=5, value=2, step=1)
        wave_tabs = st.tabs([f"🌊 Wave {i+1}" for i in range(num_waves)])
        wave_configs = {}
        
        for i, tab in enumerate(wave_tabs):
            with tab:
                st.subheader(f"Parameters for Rally Wave #{i+1}")
                w_col1, w_col2 = st.columns(2)
                
                with w_col1:
                    # --- NEW: Unified Wave Troop Level ---
                    st.markdown("**Wave Base Troop Level**")
                    wc1, wc2 = st.columns(2)
                    w_tier = wc1.selectbox("Wave Tier", range(1, 12), index=9, key=f"wtier_{i}") # Default T10
                    w_tg = wc2.selectbox("Wave TG", range(0, 6), index=5, key=f"wtg_{i}")       # Default TG5
                    st.markdown("---")
                    
                    st.markdown("**Troop Configuration**")
                    a_inf = st.number_input("Infantry Count", value=600000, key=f"w_inf_{i}")
                    a_cav = st.number_input("Cavalry Count", value=200000, key=f"w_cav_{i}")
                    a_arc = st.number_input("Archer Count", value=200000, key=f"w_arc_{i}")
                    
                # ... (Wave Heroes and Stats expanders remain the same) ...
                
                # Update wave_configs dictionary to store the locked tier/tg instead of ratios
                with st.expander(f"📊 Wave {i+1} Core Combat Stats Override"):
                    # ... (Stats inputs remain the same) ...
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

        # =========================================================================
        # --- EXECUTION LOOP ---
        # =========================================================================
        if st.button("🚀 Run Multi-Rally Simulation Sequence"):
            with st.spinner("Processing continuous battlefield math blocks..."):
                
                garrison_widgets = [g_wid1, g_wid2, g_wid3, 0, 0, 0, 0]
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
                    tier=g_tier,          # NEW
                    tg_level=g_tg,        # NEW
                    widget_levels=garrison_widgets
                )
                
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
                        tier=w_data["tier"],     # NEW
                        tg_level=w_data["tg"],   # NEW
                        widget_levels=w_data["widgets"]
                    )
                    rally_waves_input.append(wave_setup)

                # ... (The Monte Carlo looping logic remains exactly the same) ...

                # 3. Process tracking arrays over the complete simulation run
                garrison_survivors_total = 0
                garrison_breakdown_avg = np.zeros(3)
                
                wave_survivor_tracking = {w: 0 for w in range(num_waves)}
                wave_win_counts = {w: 0 for w in range(num_waves)} # Tracks exact win probability

                for _ in range(int(num_runs)):
                    temp_garrison = copy.deepcopy(garrison_setup)
                    temp_waves = copy.deepcopy(rally_waves_input)
                    
                    final_garrison, logs = kingshot_multirally_sim2(temp_waves, temp_garrison)
                    
                    garrison_survivors_total += np.sum(final_garrison.troops)
                    garrison_breakdown_avg += final_garrison.troops
                    
                    for step_idx, log in enumerate(logs):
                        att_surv = np.sum(log['attacker_surviving'])
                        wave_survivor_tracking[step_idx] += att_surv
                        
                        # If attackers have troops left, they "won" this specific combat wave
                        if att_surv > 0:
                            wave_win_counts[step_idx] += 1

                # 4. Generate Averages
                avg_g_survivors = garrison_survivors_total / num_runs
                avg_g_breakdown = garrison_breakdown_avg / num_runs

                # =========================================================================
                # --- RESULTS DISPLAY ---
                # =========================================================================
                st.success("Simulation Sequence Complete!")
                
                # Check win condition based on whether the final garrison was wiped
                if avg_g_survivors <= 0:
                    st.markdown("### 🏆 STATUS: <span style='color:red'>GARRISON COMPLETELY BROKEN</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"### 🏰 STATUS: <span style='color:green'>GARRISON HELD (Avg. {avg_g_survivors:,.0f} Total Troops Left)</span>", unsafe_allow_html=True)

                out_col1, out_col2 = st.columns(2)
                
                with out_col1:
                    st.markdown("#### 🛡️ Final Defense Status")
                    st.table({
                        "Troop Class": ["Frontline Infantry", "Flanking Cavalry", "Backend Archers", "Total Remaining"],
                        "Remaining (Avg)": [
                            f"{avg_g_breakdown[0]:,.0f}", 
                            f"{avg_g_breakdown[1]:,.0f}", 
                            f"{avg_g_breakdown[2]:,.0f}",
                            f"{avg_g_survivors:,.0f}" # Summed up automatically
                        ]
                    })
                    
                with out_col2:
                    st.markdown("#### 🚀 Attacker Wave Performance")
                    wave_perf_display = []
                    for w_idx in range(num_waves):
                        avg_w_surv = wave_survivor_tracking[w_idx] / num_runs
                        win_rate_percent = (wave_win_counts[w_idx] / num_runs) * 100
                        
                        wave_perf_display.append({
                            "Rally Wave": f"Wave #{w_idx + 1}",
                            "Win Rate %": f"{win_rate_percent:.1f}%", # Shows literal probability of success
                            "Avg Retained Troops": f"{avg_w_surv:,.0f}"
                        })
                    st.table(wave_perf_display)