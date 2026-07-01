# app.py

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json

from src.config import GRID_SIZE, get_grid_coords, FEATURES, REGIONS, latlon_to_grid, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
from src.data_ingestion import ClimateDataIngestor
from src.digital_twin import ClimateDigitalTwin
from src.anomaly_detector import AnomalyDetector
from src.predictor import ClimatePredictionEngine
from src.simulation_engine import ClimateSimulationEngine
from src.optimizer import DecisionOptimizer
from src.resource_allocator import ResourceAllocator
from src.output_generator import OutputGenerator

# Page Setup
st.set_page_config(
    page_title="BHARAT CLIMATE TWIN",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Injections for Premium Aesthetics
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
    /* Main App Customization */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .reportview-container {
        background: #0B0F19;
    }
    
    /* Custom Headers */
    .app-title {
        font-weight: 700;
        font-size: 2.8rem;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    
    .app-subtitle {
        font-weight: 300;
        font-size: 1.1rem;
        color: #8C9FC2;
        margin-top: 0px;
        margin-bottom: 25px;
    }

    /* Glassmorphic Containers */
    .glass-card {
        background: rgba(22, 28, 45, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .glass-header {
        font-weight: 600;
        color: #E2E8F0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 8px;
        margin-bottom: 16px;
        font-size: 1.25rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Alerts and Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-live {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        animation: pulse 2s infinite;
    }

    .badge-paused {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .severity-extreme {
        background: rgba(239, 68, 68, 0.2);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    
    .severity-high {
        background: rgba(249, 115, 22, 0.2);
        color: #FDBA74;
        border: 1px solid rgba(249, 115, 22, 0.4);
    }

    .severity-medium {
        background: rgba(234, 179, 8, 0.15);
        color: #FDE047;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }

    .severity-low {
        background: rgba(59, 130, 246, 0.15);
        color: #93C5FD;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* Keyframes for animations */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1.0; }
        100% { opacity: 0.6; }
    }
    
    /* Interactive custom boxes */
    .alert-box {
        background: rgba(239, 68, 68, 0.08);
        border-left: 4px solid #EF4444;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    
    .alert-title {
        font-weight: 600;
        color: #F87171;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    
    .alert-desc {
        color: #FCA5A5;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "ingestor" not in st.session_state:
    st.session_state.ingestor = ClimateDataIngestor()
    st.session_state.twin = ClimateDigitalTwin(history_len=10)
    st.session_state.detector = AnomalyDetector()
    st.session_state.predictor = ClimatePredictionEngine(st.session_state.detector)
    st.session_state.sim_engine = ClimateSimulationEngine(st.session_state.twin, st.session_state.detector)
    st.session_state.optimizer = DecisionOptimizer(st.session_state.sim_engine)
    st.session_state.allocator = ResourceAllocator()
    st.session_state.generator = OutputGenerator()
    
    # Control flags
    st.session_state.loop_running = True
    st.session_state.tick = 0
    
    # Warm up twin with initial buffer
    for _ in range(5):
        grid = st.session_state.ingestor.ingest_current_state(base_state=st.session_state.twin.current_state)
        st.session_state.twin.update_state(grid)

# Shortcuts to states
ingestor = st.session_state.ingestor
twin = st.session_state.twin
detector = st.session_state.detector
predictor = st.session_state.predictor
optimizer = st.session_state.optimizer
allocator = st.session_state.allocator
generator = st.session_state.generator

# --- HEADER SECTION ---
col1, col2 = st.columns([8, 2], vertical_alignment="center")
with col1:
    st.markdown('<h1 class="app-title">🌍 BHARAT CLIMATE TWIN</h1>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">AI Climate Digital Twin of India & Simulation-Based Decision Optimizer</p>', unsafe_allow_html=True)
with col2:
    if st.session_state.loop_running:
        st.markdown('<div style="text-align: right;"><span class="badge badge-live">🔴 Continuous Loop Running</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align: right;"><span class="badge badge-paused">⏸️ Simulation Paused</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right; color: #8C9FC2; font-size: 0.85rem; margin-top: 8px;">Tick Step: {st.session_state.tick}</div>', unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/bd/Indian_Space_Research_Organisation_Logo.svg", width=80)
    st.markdown("### Control & Ingestion")
    
    # Real-time state injection triggers
    trigger_sel = st.selectbox(
        "Inject Meteorological Event",
        options=["Normal Weather", "Cyclone (Odisha Coast)", "Heatwave (North Plains)", "Monsoon Downpour (Mumbai)", "Severe Drought (Deccan)"],
        index=0
    )
    
    if trigger_sel == "Normal Weather":
        ingestor.clear_trigger()
    elif trigger_sel == "Cyclone (Odisha Coast)":
        ingestor.set_disaster_trigger("cyclone", center_lat=(20.0, 86.5), intensity=1.5)
    elif trigger_sel == "Heatwave (North Plains)":
        ingestor.set_disaster_trigger("heatwave", center_lat=(28.0, 75.0), intensity=1.6)
    elif trigger_sel == "Monsoon Downpour (Mumbai)":
        ingestor.set_disaster_trigger("monsoon", center_lat=(19.0, 72.8), intensity=1.8)
    elif trigger_sel == "Severe Drought (Deccan)":
        ingestor.set_disaster_trigger("drought", center_lat=(15.5, 76.5), intensity=1.4)
        
    st.divider()
    
    # Loop controls
    st.markdown("### Simulation Loop Controls")
    col_play, col_pause = st.columns(2)
    with col_play:
        if st.button("▶️ Resume Loop", width='stretch'):
            st.session_state.loop_running = True
            st.rerun()
    with col_pause:
        if st.button("⏸️ Pause Loop", width='stretch'):
            st.session_state.loop_running = False
            st.rerun()
            
    loop_speed = st.slider("Step Update Delay (s)", min_value=1.0, max_value=6.0, value=2.0)
    
    st.divider()
    
    # Optimizer weight sliders
    st.markdown("### AI Action Weights")
    st.markdown("<small>Configure criteria weights for mitigating disasters</small>", unsafe_allow_html=True)
    w_risk = st.slider("Risk Reduction Weight", 0.0, 1.0, 0.45, step=0.05)
    w_cost = st.slider("Cost Limit Weight", 0.0, 1.0, 0.20, step=0.05)
    w_feas = st.slider("Feasibility Weight", 0.0, 1.0, 0.15, step=0.05)
    w_time = st.slider("Response Speed Weight", 0.0, 1.0, 0.20, step=0.05)
    
    weights = {"risk": w_risk, "cost": w_cost, "feasibility": w_feas, "time": w_time}

# --- STEP UPDATE ---
# Perform one simulation step if loop is active
if st.session_state.loop_running:
    grid = ingestor.ingest_current_state(base_state=twin.current_state)
    twin.update_state(grid)
    st.session_state.tick += 1
    
# Gather current alerts
active_anomalies = detector.detect_anomalies(twin.current_state, ingestor.ocean_mask)
predicted_anomalies = predictor.predict_disasters(twin.get_history(), ingestor.ocean_mask)

# Layout Setup: 2-column core dashboard
col_map, col_details = st.columns([6, 4])

with col_map:
    # --- GEOSPATIAL MAP PANEL ---
    st.markdown("""
    <div class="glass-card">
        <div class="glass-header">🗺️ Spatio-Temporal Climate Map</div>
    </div>
    """, unsafe_allow_html=True)
    
    map_feature = st.selectbox(
        "Display Climate Layer",
        options=["Rainfall (mm/hr)", "Air Temperature (°C)", "Sea Surface Temperature (°C)", "Cloud Cover (%)", "Wind Speed (km/h)", "Soil Moisture (%)"],
        index=0
    )
    
    # Map feature conversion
    feature_mapping = {
        "Rainfall (mm/hr)": (0, "rainbow", 0.0, 45.0),
        "Air Temperature (°C)": (1, "thermal", 10.0, 50.0),
        "Sea Surface Temperature (°C)": (2, "ice", 15.0, 32.0),
        "Cloud Cover (%)": (3, "gray", 0.0, 1.0),
        "Wind Speed (km/h)": (5, "blues", 0.0, 120.0),
        "Soil Moisture (%)": (4, "tealgrn", 0.0, 1.0)
    }
    feat_idx, colorscale, vmin, vmax = feature_mapping[map_feature]
    
    # Generate coordinates grid
    lats, lons = get_grid_coords()
    grid_display = twin.current_state[:, :, feat_idx]
    
    # For nicer visuals, let's create a Plotly Heatmap
    # Coordinates mapping is Lat (y) vs Lon (x)
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=grid_display,
        x=lons,
        y=lats,
        colorscale=colorscale,
        colorbar=dict(title=map_feature),
        zmin=vmin,
        zmax=vmax,
        opacity=0.85
    ))
    
    # Plot cities and active alerts
    for name, coords in REGIONS.items():
        # Check if anomaly is active at this city
        # Nearest grid pos
        row, col = latlon_to_grid(coords[0], coords[1])
        local_anomaly = next((a for a in active_anomalies if a["grid_pos"] == (row, col)), None)
        
        # Color marker depending on threat
        marker_color = "#38BDF8" # clear cyan
        marker_size = 8
        if local_anomaly:
            marker_color = "#EF4444" # red
            marker_size = 14
            
        fig.add_trace(go.Scatter(
            x=[coords[1]],
            y=[coords[0]],
            mode="markers+text",
            marker=dict(size=marker_size, color=marker_color, line=dict(width=1.5, color="white")),
            text=[name],
            textposition="top center",
            name=name,
            hoverinfo="text",
            textfont=dict(color="white", size=10)
        ))
        
    # Plot forecast zones for predicted disasters (T+...)
    for idx, pred in enumerate(predicted_anomalies):
        plat, plon = pred["location_coord"]
        fig.add_trace(go.Scatter(
            x=[plon],
            y=[plat],
            mode="markers",
            marker=dict(size=18, symbol="star", color="#F59E0B", line=dict(width=1, color="white")),
            hovertext=f"Predicted: {pred['event_type'].upper()} ({pred['time_window']})",
            name=f"Forecast-{idx}"
        ))

    fig.update_layout(
        xaxis=dict(title="Longitude (°E)", gridcolor="rgba(255,255,255,0.05)", range=[LON_MIN, LON_MAX]),
        yaxis=dict(title="Latitude (°N)", gridcolor="rgba(255,255,255,0.05)", range=[LAT_MIN, LAT_MAX]),
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Sensor cards/Metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    
    # Calculate statistics from current state
    avg_temp = np.mean(twin.current_state[:, :, 1])
    max_rain = np.max(twin.current_state[:, :, 0])
    avg_humidity = np.mean(twin.current_state[:, :, 6])
    
    with col_m1:
        st.metric(label="🌡️ Avg Land Temperature", value=f"{avg_temp:.1f} °C", delta=f"{avg_temp - 28.5:.1f} °C vs normal")
    with col_m2:
        st.metric(label="🌧️ Max Local Precipitation", value=f"{max_rain:.1f} mm/hr", delta="Active front" if max_rain > 5.0 else "Stable")
    with col_m3:
        st.metric(label="💧 Avg Ambient Humidity", value=f"{avg_humidity:.1f} %")

with col_details:
    # --- SIDE DETAILS / TABS PANEL ---
    tabs = st.tabs(["⚠️ Alerts & Predictions", "🤖 Mitigation Optimizer", "📦 Dispatch & Resources"])
    
    with tabs[0]:
        st.markdown("### Early Warning & Prediction Engine")
        
        # Display active alarms
        st.markdown("#### Current Active Anomalies")
        if not active_anomalies:
            st.info("✅ No active climate anomalies detected across the grid.")
        else:
            for a in active_anomalies:
                severity_class = f"severity-{a['severity']}"
                st.markdown(f"""
                <div class="alert-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="alert-title">🚨 Active {a['type'].capitalize()} Detected</span>
                        <span class="badge {severity_class}">{a['severity']}</span>
                    </div>
                    <div class="alert-desc">
                        Location: Lat {a['lat']:.2f}, Lon {a['lon']:.2f}<br/>
                        Confidence: {a['confidence']:.1f}% | Metrics: {', '.join([f'{k}: {v:.1f}' for k,v in a['metrics'].items()])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        # Display future forecasts
        st.markdown("#### Predictive Forecast Models (T+6h to T+48h)")
        if not predicted_anomalies:
            st.success("🌤️ Forecasting models show stable conditions for the next 48 hours.")
        else:
            for p in predicted_anomalies:
                severity_class = f"severity-{p['severity']}"
                st.markdown(f"""
                <div class="glass-card" style="padding: 12px; margin-bottom: 10px; border-left: 4px solid #F59E0B;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #F59E0B;">🔮 Predicted {p['event_type'].capitalize()}</span>
                        <span class="badge {severity_class}">{p['severity']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; margin-top: 4px;">
                        Location: Lat {p['location_coord'][0]:.2f}, Lon {p['location_coord'][1]:.2f}<br/>
                        Timeline window: <b>{p['time_window']}</b><br/>
                        AI Forecast Confidence: <b>{p['confidence']:.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show explainability report in expander
                with st.expander(f"Explainability Diagnostic: Why this {p['event_type']}?"):
                    report = generator.generate_explainability_report(p)
                    st.markdown(report)

    with tabs[1]:
        st.markdown("### AI Action & Simulation Optimizer")
        
        # Trigger mitigation optimizer if there is an active anomaly
        # Use first active anomaly or first predicted anomaly to demonstrate
        target_anomaly = None
        if active_anomalies:
            target_anomaly = active_anomalies[0]
            st.markdown(f"**Mitigating Active Event:** `{target_anomaly['type'].capitalize()}` at Lat {target_anomaly['lat']:.2f}, Lon {target_anomaly['lon']:.2f}")
        elif predicted_anomalies:
            target_anomaly = predicted_anomalies[0]
            st.markdown(f"**Mitigating Forecasted Event:** `{target_anomaly['event_type'].capitalize()}` ({target_anomaly['time_window']})")
            
        if not target_anomaly:
            st.info("💡 Optimizer is on Standby. Inject a weather event/disaster to trigger mitigation simulation.")
        else:
            # Run simulation & optimizer
            opt_result = optimizer.optimize_decision(target_anomaly, ingestor.ocean_mask, weights)
            recommended = opt_result["recommended"]
            options = opt_result["all_options"]
            
            if recommended:
                st.markdown(f"""
                <div class="glass-card" style="border: 2px solid #10B981; background: rgba(16, 185, 129, 0.05); padding: 16px;">
                    <div style="font-weight: 700; color: #34D399; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                        🏆 RECOMMENDED STRATEGY
                    </div>
                    <h3 style="margin: 8px 0px; color: white;">{recommended['strategy_name']}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem; color: #E2E8F0; margin-top: 8px;">
                        <div>🛡️ Risk Reduction: <b>{recommended['risk_reduction_pct']}%</b></div>
                        <div>💳 Est. Cost: <b>${recommended['cost']:,}</b></div>
                        <div>🛠️ Feasibility Score: <b>{recommended['feasibility_score']*100:.0f}%</b></div>
                        <div>⏱️ Speed Index: <b>{recommended['time_efficiency']*100:.0f}%</b></div>
                    </div>
                    <div style="font-weight: 600; color: #10B981; font-size: 0.9rem; margin-top: 12px; text-align: right;">
                        Recommendation Utility Score: {recommended['utility_score']:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Plotly Chart comparing strategies
                st.markdown("#### Simulated Strategy Utility Scores")
                names = [o["strategy_name"] for o in options]
                scores = [o["utility_score"] for o in options]
                reductions = [o["risk_reduction_pct"] for o in options]
                
                fig_opt = go.Figure()
                fig_opt.add_trace(go.Bar(
                    y=names,
                    x=scores,
                    orientation='h',
                    marker=dict(color='rgba(79, 172, 254, 0.8)', line=dict(color='rgba(79, 172, 254, 1.0)', width=1.5)),
                    name="Utility Score (%)"
                ))
                fig_opt.add_trace(go.Bar(
                    y=names,
                    x=reductions,
                    orientation='h',
                    marker=dict(color='rgba(16, 185, 129, 0.4)', line=dict(color='rgba(16, 185, 129, 0.6)', width=1.5)),
                    name="Risk Reduction (%)"
                ))
                
                fig_opt.update_layout(
                    barmode='group',
                    height=240,
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="%"),
                    yaxis=dict(autorange="reversed"),
                    legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_opt, width='stretch')

    with tabs[2]:
        st.markdown("### Government Action Dispatcher")
        
        target_anomaly = None
        if active_anomalies:
            target_anomaly = active_anomalies[0]
        elif predicted_anomalies:
            target_anomaly = predicted_anomalies[0]
            
        if not target_anomaly:
            st.info("💡 Dispatcher on standby. Active or predicted hazards required to format output alerts.")
        else:
            # Re-run optimizer to pass recommendation details
            opt_result = optimizer.optimize_decision(target_anomaly, ingestor.ocean_mask, weights)
            recommended = opt_result["recommended"]
            
            # 1. SMS/Notification Broadcast Output
            st.markdown("#### 📱 Emergency Broadcast Notification (SMS)")
            sms_text = generator.generate_sms_alert(target_anomaly, recommended)
            st.code(sms_text, language="text")
            
            # 2. Responders Action Checklist
            st.markdown("#### 📋 Step-by-Step Response Checklist")
            checklist = generator.generate_action_checklist(target_anomaly, recommended)
            for item in checklist:
                st.markdown(item)
                
            # 3. Rescue Assets & Resources
            st.markdown("#### 🚒 Estimated Emergency Resource Allocation")
            res_allocation = allocator.allocate_resources(target_anomaly)
            
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #8C9FC2; margin-bottom: 10px;">
                Impact Zone Category: <b>{res_allocation['affected_region']}</b><br/>
                Proximity Multiplier: <b>{res_allocation['density_multiplier']}x</b> | Severity Multiplier: <b>{res_allocation['severity_multiplier']}x</b>
            </div>
            """, unsafe_allow_html=True)
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown(f"👨‍🚒 **NDRF Rescue Teams:** `{res_allocation['rescue_teams']} units`")
                st.markdown(f"🚑 **Ambulances:** `{res_allocation['ambulances']} dispatch`")
                st.markdown(f"⛺ **Relief Camps:** `{res_allocation['relief_camps']} sites`")
            with col_a2:
                st.markdown(f"🍱 **Food Supplies:** `{res_allocation['food_supply_kg']:,} kg/day`")
                st.markdown(f"🚰 **Drinking Water:** `{res_allocation['water_supply_liters']:,} L/day`")
                st.markdown(f"🏥 **Mobile Medicals:** `{res_allocation['medical_units']} units`")
                
            # 4. GIS GeoJSON Output Download
            st.markdown("#### 🌐 GIS Integration Map Files")
            geojson_data = generator.generate_geojson(target_anomaly)
            geojson_str = json.dumps(geojson_data, indent=2)
            st.download_button(
                label="📥 Download GeoJSON Alert Polygon",
                data=geojson_str,
                file_name="climate_twin_alert.geojson",
                mime="application/json",
                width='stretch'
            )

# Continuous updating loop sleep & refresh
if st.session_state.loop_running:
    time.sleep(loop_speed)
    st.rerun()
