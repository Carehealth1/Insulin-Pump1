"""
Enhanced Insulin Pump Therapy Educational Platform
Interactive Patient Journey Learning Module with Adjustment Controls

Author: Claude AI Assistant
Purpose: Interactive learning platform for insulin pump management with real adjustments
Features: Basal rate adjustments, I:C ratio changes, professor scenario builder
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random
import json
import copy

# Set page configuration
st.set_page_config(
    page_title="Insulin Pump Therapy Learning Platform",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .patient-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #4f46e5;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .pump-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.25rem 0.25rem 0 0;
        color: white;
    }
    .adjustment-panel {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
    }
    .decision-point {
        background: #fef3c7;
        border: 2px solid #f59e0b;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
    }
    .success-outcome {
        background: #d1fae5;
        border: 2px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #065f46;
    }
    .warning-outcome {
        background: #fef2f2;
        border: 2px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #7f1d1d;
    }
    .info-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #1e40af;
        margin: 1rem 0;
    }
    .comparison-box {
        background: #fafafa;
        border: 1px solid #d1d5db;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'current_week' not in st.session_state:
    st.session_state.current_week = 0
if 'patient_progress' not in st.session_state:
    st.session_state.patient_progress = {}
if 'learning_stats' not in st.session_state:
    st.session_state.learning_stats = {
        'patients_completed': 0,
        'adjustments_made': 0,
        'successful_outcomes': 0
    }
if 'current_glucose_data' not in st.session_state:
    st.session_state.current_glucose_data = None
if 'adjustment_made' not in st.session_state:
    st.session_state.adjustment_made = False
if 'custom_scenarios' not in st.session_state:
    st.session_state.custom_scenarios = []
if 'professor_mode' not in st.session_state:
    st.session_state.professor_mode = False

# Enhanced glucose data generation with insulin sensitivity
def generate_glucose_data(days=7, basal_rates=None, issues=None, ic_ratios=None, correction_factor=50, week=0):
    """Generate realistic CGM-style glucose data based on pump settings"""
    np.random.seed(42 + week)  # Vary by week for progression
    
    timestamps = pd.date_range(start='2024-01-01', periods=days*288, freq='5min')
    glucose_values = []
    
    # Default basal rates if none provided
    if basal_rates is None:
        basal_rates = [0.8] * 24
    
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        minute = ts.minute
        
        # Get current basal rate effect
        current_basal = basal_rates[hour]
        basal_effect = current_basal * 50  # Rough conversion to glucose effect
        
        # Base glucose pattern based on time of day
        if 6 <= hour <= 8:  # Dawn phenomenon
            base_glucose = 140 + np.random.normal(0, 15) - basal_effect
        elif 12 <= hour <= 14:  # Post-lunch
            base_glucose = 160 + np.random.normal(0, 20) - basal_effect
        elif 18 <= hour <= 20:  # Post-dinner
            base_glucose = 150 + np.random.normal(0, 18) - basal_effect
        elif 2 <= hour <= 4:  # Overnight
            base_glucose = 95 + np.random.normal(0, 10) - basal_effect
        else:
            base_glucose = 120 + np.random.normal(0, 12) - basal_effect
        
        # Apply specific issues if present and week < 4 (before major adjustments)
        if issues and week < 4:
            if 'dawn_phenomenon' in issues and 4 <= hour <= 7:
                base_glucose += max(0, 40 - (week * 10))  # Reduce over time
            elif 'afternoon_lows' in issues and 14 <= hour <= 16:
                base_glucose -= max(0, 30 - (week * 7))
            elif 'post_meal_spikes' in issues and (hour in [13, 19]):
                spike_reduction = week * 15 if ic_ratios else 0
                base_glucose += max(20, 80 - spike_reduction)
            elif 'nocturnal_lows' in issues and 1 <= hour <= 3:
                base_glucose -= max(0, 25 - (week * 6))
            elif 'hypoglycemia_unawareness' in issues and np.random.random() < 0.05:
                base_glucose -= 40
        
        # Meal bolus effects based on I:C ratios
        if minute == 0 and hour in [7, 12, 18]:  # Meal times
            meal_carbs = np.random.normal(45, 15)  # Average meal carbs
            if ic_ratios:
                meal_key = ['breakfast', 'lunch', 'dinner'][hour//7 if hour < 14 else (1 if hour < 17 else 2)]
                if meal_key in ic_ratios:
                    insulin_needed = meal_carbs / ic_ratios[meal_key]
                    glucose_drop = insulin_needed * correction_factor
                    base_glucose = base_glucose + 80 - glucose_drop  # Post-meal rise minus insulin effect
                else:
                    base_glucose += 60  # Uncontrolled rise
            else:
                base_glucose += 60
        
        # Ensure glucose stays in reasonable bounds
        base_glucose = max(40, min(400, base_glucose))
        glucose_values.append(base_glucose)
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'glucose': glucose_values
    })

# Mock patient data with comprehensive pump settings
PUMP_PATIENTS = [
    {
        'id': 'pump-001',
        'name': 'Sarah Chen',
        'age': 28,
        'gender': 'Female',
        'mrn': 'PT001',
        'diabetes_type': 'Type 1',
        'duration_diabetes': '15 years',
        'pump_type': 'Tandem t:slim X2',
        'cgm_type': 'Dexcom G6',
        'algorithm': 'Control-IQ',
        'original_settings': {
            'basal_profile': [0.8, 0.6, 0.5, 0.5, 0.9, 1.2, 1.0, 0.8, 0.7, 0.7, 0.8, 0.9, 
                            1.0, 0.8, 0.7, 0.6, 0.8, 1.1, 1.0, 0.9, 0.8, 0.8, 0.8, 0.8],
            'ic_ratios': {'breakfast': 12, 'lunch': 15, 'dinner': 10},
            'correction_factor': 50,
            'target_glucose': 110
        },
        'current_settings': {
            'basal_profile': [0.8, 0.6, 0.5, 0.5, 0.9, 1.2, 1.0, 0.8, 0.7, 0.7, 0.8, 0.9, 
                            1.0, 0.8, 0.7, 0.6, 0.8, 1.1, 1.0, 0.9, 0.8, 0.8, 0.8, 0.8],
            'ic_ratios': {'breakfast': 12, 'lunch': 15, 'dinner': 10},
            'correction_factor': 50,
            'target_glucose': 110
        },
        'scenario': 'dawn_phenomenon',
        'description': 'Active professional with consistent dawn phenomenon requiring basal optimization',
        'clinical_notes': 'Patient reports morning glucose consistently 180-220 mg/dL despite overnight target range. Needs early morning basal adjustment.',
        'a1c_trend': [7.8, 7.5, 7.2],
        'learning_objectives': [
            'Recognize dawn phenomenon pattern in CGM data',
            'Calculate appropriate basal rate increases for early morning',
            'Monitor response to basal adjustments over time'
        ]
    },
    {
        'id': 'pump-002',
        'name': 'Miguel Rodriguez',
        'age': 34,
        'gender': 'Male',
        'mrn': 'PT002',
        'diabetes_type': 'Type 1',
        'duration_diabetes': '8 years',
        'pump_type': 'Omnipod 5',
        'cgm_type': 'Dexcom G6',
        'algorithm': 'SmartAdjust',
        'original_settings': {
            'basal_profile': [0.9, 0.8, 0.7, 0.7, 0.8, 0.9, 1.1, 0.9, 0.8, 0.8, 0.9, 1.0,
                            1.2, 1.0, 0.6, 0.5, 0.8, 1.0, 1.1, 1.0, 0.9, 0.9, 0.9, 0.9],
            'ic_ratios': {'breakfast': 10, 'lunch': 12, 'dinner': 8},
            'correction_factor': 45,
            'target_glucose': 120
        },
        'current_settings': {
            'basal_profile': [0.9, 0.8, 0.7, 0.7, 0.8, 0.9, 1.1, 0.9, 0.8, 0.8, 0.9, 1.0,
                            1.2, 1.0, 0.6, 0.5, 0.8, 1.0, 1.1, 1.0, 0.9, 0.9, 0.9, 0.9],
            'ic_ratios': {'breakfast': 10, 'lunch': 12, 'dinner': 8},
            'correction_factor': 45,
            'target_glucose': 120
        },
        'scenario': 'exercise_management',
        'description': 'Marathon runner struggling with exercise-induced hypoglycemia',
        'clinical_notes': 'Patient runs 6 miles daily at 4 PM. Frequent lows during and after exercise despite reducing basal. May need exercise mode optimization.',
        'a1c_trend': [6.9, 7.1, 7.3],
        'learning_objectives': [
            'Identify exercise-related hypoglycemia patterns',
            'Implement temporary basal reductions for exercise',
            'Understand delayed post-exercise hypoglycemia risk'
        ]
    },
    {
        'id': 'pump-003',
        'name': 'Jennifer Park',
        'age': 19,
        'gender': 'Female',
        'mrn': 'PT003',
        'diabetes_type': 'Type 1',
        'duration_diabetes': '3 years',
        'pump_type': 'Medtronic 780G',
        'cgm_type': 'Guardian 4',
        'algorithm': 'SmartGuard',
        'original_settings': {
            'basal_profile': [0.6, 0.5, 0.4, 0.4, 0.6, 0.8, 0.9, 0.7, 0.6, 0.7, 0.8, 0.9,
                            1.1, 1.3, 0.8, 0.7, 0.9, 1.2, 1.0, 0.8, 0.7, 0.6, 0.6, 0.6],
            'ic_ratios': {'breakfast': 15, 'lunch': 18, 'dinner': 12},
            'correction_factor': 60,
            'target_glucose': 100
        },
        'current_settings': {
            'basal_profile': [0.6, 0.5, 0.4, 0.4, 0.6, 0.8, 0.9, 0.7, 0.6, 0.7, 0.8, 0.9,
                            1.1, 1.3, 0.8, 0.7, 0.9, 1.2, 1.0, 0.8, 0.7, 0.6, 0.6, 0.6],
            'ic_ratios': {'breakfast': 15, 'lunch': 18, 'dinner': 12},
            'correction_factor': 60,
            'target_glucose': 100
        },
        'scenario': 'post_meal_spikes',
        'description': 'College student with irregular eating and persistent post-meal highs',
        'clinical_notes': 'Erratic schedule, frequent missed boluses, post-prandial spikes >300 mg/dL. Needs carb counting education and I:C ratio adjustment.',
        'a1c_trend': [8.2, 7.9, 8.1],
        'learning_objectives': [
            'Analyze post-prandial glucose patterns',
            'Adjust insulin-to-carb ratios appropriately',
            'Implement pre-bolusing strategies'
        ]
    },
    {
        'id': 'pump-004',
        'name': 'Robert Kim',
        'age': 45,
        'gender': 'Male',
        'mrn': 'PT004',
        'diabetes_type': 'Type 1',
        'duration_diabetes': '22 years',
        'pump_type': 'Tandem t:slim X2',
        'cgm_type': 'Dexcom G6',
        'algorithm': 'Control-IQ',
        'original_settings': {
            'basal_profile': [1.1, 0.9, 0.8, 0.8, 1.0, 1.3, 1.2, 1.0, 0.9, 0.9, 1.0, 1.1,
                            1.2, 1.0, 0.7, 0.6, 0.9, 1.2, 1.1, 1.0, 1.0, 1.0, 1.1, 1.1],
            'ic_ratios': {'breakfast': 8, 'lunch': 10, 'dinner': 7},
            'correction_factor': 35,
            'target_glucose': 120
        },
        'current_settings': {
            'basal_profile': [1.1, 0.9, 0.8, 0.8, 1.0, 1.3, 1.2, 1.0, 0.9, 0.9, 1.0, 1.1,
                            1.2, 1.0, 0.7, 0.6, 0.9, 1.2, 1.1, 1.0, 1.0, 1.0, 1.1, 1.1],
            'ic_ratios': {'breakfast': 8, 'lunch': 10, 'dinner': 7},
            'correction_factor': 35,
            'target_glucose': 120
        },
        'scenario': 'hypoglycemia_unawareness',
        'description': 'Long-term T1D with hypoglycemia unawareness and frequent severe lows',
        'clinical_notes': 'Multiple severe hypoglycemia episodes. Needs higher glucose targets and aggressive low prevention strategies.',
        'a1c_trend': [6.2, 6.8, 7.0],
        'learning_objectives': [
            'Recognize hypoglycemia unawareness patterns',
            'Implement conservative glucose targets',
            'Balance glycemic control with safety'
        ]
    }
]

def get_pump_color(pump_type):
    """Return color for pump type"""
    color_map = {
        'Tandem t:slim X2': '#3b82f6',
        'Omnipod 5': '#10b981',
        'Medtronic 780G': '#8b5cf6'
    }
    return color_map.get(pump_type, '#6b7280')

def render_patient_card(patient):
    """Render patient information card"""
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{patient['name']}** - {patient['age']}y {patient['gender']}")
            st.markdown(f"📋 {patient['mrn']} • {patient['diabetes_type']} • {patient['duration_diabetes']}")
            
            # Pump and algorithm badges
            pump_color = get_pump_color(patient['pump_type'])
            st.markdown(f"""
            <div style="margin-top: 8px;">
                <span class="pump-badge" style="background-color: {pump_color};">
                    {patient['pump_type']}
                </span>
                <span class="pump-badge" style="background-color: #f59e0b;">
                    {patient['algorithm']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            current_a1c = patient['a1c_trend'][-1]
            st.metric("Current A1C", f"{current_a1c}%")

def create_glucose_plot(df, title="Continuous Glucose Monitor", highlight_periods=None):
    """Create an interactive glucose plot"""
    fig = go.Figure()
    
    # Color glucose values by range
    colors = []
    for glucose in df['glucose']:
        if glucose < 70:
            colors.append('#f59e0b')  # Low - amber
        elif glucose > 180:
            colors.append('#ef4444')  # High - red  
        else:
            colors.append('#10b981')  # Target - green
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['glucose'],
        mode='lines+markers',
        name='Glucose',
        line=dict(width=2),
        marker=dict(size=3, color=colors),
        hovertemplate='%{x}<br>Glucose: %{y} mg/dL<extra></extra>'
    ))
    
    # Add target range shading
    fig.add_hrect(y0=70, y1=180, fillcolor="green", opacity=0.1, line_width=0)
    fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Low threshold")
    fig.add_hline(y=180, line_dash="dash", line_color="red", annotation_text="High threshold")
    
    # Highlight specific periods if provided
    if highlight_periods:
        for period in highlight_periods:
            fig.add_vrect(
                x0=period['start'], x1=period['end'],
                fillcolor=period.get('color', 'yellow'), opacity=0.2,
                annotation_text=period.get('label', ''), annotation_position="top left"
            )
    
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Glucose (mg/dL)',
        height=400,
        showlegend=False,
        yaxis=dict(range=[40, 400])
    )
    
    return fig

def calculate_glucose_metrics(df):
    """Calculate key glucose metrics"""
    metrics = {}
    metrics['time_in_range'] = len(df[(df['glucose'] >= 70) & (df['glucose'] <= 180)]) / len(df) * 100
    metrics['time_below_70'] = len(df[df['glucose'] < 70]) / len(df) * 100
    metrics['time_above_180'] = len(df[df['glucose'] > 180]) / len(df) * 100
    metrics['mean_glucose'] = df['glucose'].mean()
    metrics['gmi'] = (3.31 + 0.02392 * metrics['mean_glucose'])  # Glucose Management Indicator
    metrics['cv'] = (df['glucose'].std() / metrics['mean_glucose']) * 100  # Coefficient of variation
    
    return metrics

def render_glucose_metrics(metrics):
    """Display glucose metrics in a nice format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tir_color = "🟢" if metrics['time_in_range'] > 70 else "🟡" if metrics['time_in_range'] > 50 else "🔴"
        st.metric(
            "Time in Range", 
            f"{metrics['time_in_range']:.1f}%",
            help="Target: >70% (70-180 mg/dL)"
        )
        st.write(f"{tir_color}")
    
    with col2:
        low_color = "🟢" if metrics['time_below_70'] < 4 else "🟡" if metrics['time_below_70'] < 10 else "🔴"
        st.metric(
            "Time Below 70", 
            f"{metrics['time_below_70']:.1f}%",
            help="Target: <4%"
        )
        st.write(f"{low_color}")
    
    with col3:
        st.metric(
            "Mean Glucose", 
            f"{metrics['mean_glucose']:.0f} mg/dL"
        )
    
    with col4:
        st.metric(
            "GMI (est. A1C)", 
            f"{metrics['gmi']:.1f}%",
            help="Glucose Management Indicator"
        )

def create_adjustment_interface(patient, week):
    """Create interactive interface for making pump adjustments"""
    st.markdown(f"""
    <div class="adjustment-panel">
        <h3>🎯 Week {week + 1} - Interactive Pump Adjustments</h3>
        <p>Review the glucose patterns above and adjust the pump settings below. Your changes will be reflected in real-time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different adjustment types
    adj_tabs = st.tabs(["📊 Basal Rates", "🍽️ I:C Ratios", "💉 Correction Factor", "🎯 Target Glucose"])
    
    settings_changed = False
    
    with adj_tabs[0]:
        st.subheader("Hourly Basal Rate Adjustments (Units/hour)")
        st.write("**Clinical Note:** Basal rates should typically be adjusted by 10-20% increments. Consider circadian patterns.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            # Create input fields for basal rates
            new_basal = []
            for hour in range(24):
                current_rate = patient['current_settings']['basal_profile'][hour]
                new_rate = st.number_input(
                    f"{hour:02d}:00 - {hour+1:02d}:00",
                    min_value=0.0,
                    max_value=5.0,
                    value=current_rate,
                    step=0.1,
                    key=f"basal_{hour}",
                    format="%.1f"
                )
                new_basal.append(new_rate)
                if new_rate != current_rate:
                    settings_changed = True
        
        with col2:
            st.write("**Safety Guidelines:**")
            st.write("• Maximum single rate: 5.0 U/hr")
            st.write("• Typical adjustments: ±0.1-0.3 U/hr")
            st.write("• Dawn phenomenon: Increase 3-7 AM")
            st.write("• Exercise periods: Decrease 1-2 hrs before")
            
            if st.button("📈 Visualize Basal Profile"):
                basal_df = pd.DataFrame({
                    'Hour': range(24),
                    'Original': patient['original_settings']['basal_profile'],
                    'Current': new_basal
                })
                fig = px.line(basal_df, x='Hour', y=['Original', 'Current'], 
                             title="Basal Rate Comparison")
                st.plotly_chart(fig, use_container_width=True)
        
        if settings_changed:
            patient['current_settings']['basal_profile'] = new_basal
    
    with adj_tabs[1]:
        st.subheader("Insulin-to-Carbohydrate Ratios")
        st.write("**Clinical Note:** Lower numbers mean more insulin per gram of carb (stronger ratio).")
        
        col1, col2 = st.columns(2)
        with col1:
            for meal in ['breakfast', 'lunch', 'dinner']:
                current_ratio = patient['current_settings']['ic_ratios'][meal]
                new_ratio = st.number_input(
                    f"{meal.title()} (1 unit per X grams carbs)",
                    min_value=5,
                    max_value=30,
                    value=current_ratio,
                    step=1,
                    key=f"ic_{meal}"
                )
                if new_ratio != current_ratio:
                    patient['current_settings']['ic_ratios'][meal] = new_ratio
                    settings_changed = True
        
        with col2:
            st.write("**Adjustment Guidelines:**")
            st.write("• If post-meal BG >180: Strengthen ratio (lower number)")
            st.write("• If post-meal BG <70: Weaken ratio (higher number)")
            st.write("• Typical range: 8-20 grams per unit")
            st.write("• Morning often needs strongest ratio")
    
    with adj_tabs[2]:
        st.subheader("Correction Factor (Insulin Sensitivity)")
        current_cf = patient['current_settings']['correction_factor']
        new_cf = st.number_input(
            "Correction Factor (1 unit drops BG by X mg/dL)",
            min_value=20,
            max_value=100,
            value=current_cf,
            step=5,
            key="correction_factor"
        )
        if new_cf != current_cf:
            patient['current_settings']['correction_factor'] = new_cf
            settings_changed = True
        
        st.write(f"**Current Setting:** 1 unit drops BG by {new_cf} mg/dL")
        st.write("**Guidelines:** Lower numbers = more insulin-sensitive, Higher numbers = more insulin-resistant")
    
    with adj_tabs[3]:
        st.subheader("Target Glucose Level")
        current_target = patient['current_settings']['target_glucose']
        new_target = st.number_input(
            "Target Glucose (mg/dL)",
            min_value=80,
            max_value=150,
            value=current_target,
            step=5,
            key="target_glucose"
        )
        if new_target != current_target:
            patient['current_settings']['target_glucose'] = new_target
            settings_changed = True
        
        st.write("**Note:** Higher targets reduce hypoglycemia risk but may increase A1C")
    
    return settings_changed

def create_professor_interface():
    """Create interface for professors to build custom scenarios"""
    st.markdown("## 👨‍🏫 Professor Mode - Scenario Builder")
    
    scenario_tabs = st.tabs(["📝 Create New Scenario", "📚 Manage Scenarios", "📊 Student Analytics"])
    
    with scenario_tabs[0]:
        st.subheader("Build Custom Patient Scenario")
        
        with st.form("scenario_builder"):
            # Patient demographics
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Patient Name", "Custom Patient")
                age = st.number_input("Age", min_value=10, max_value=80, value=25)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                diabetes_duration = st.text_input("Diabetes Duration", "5 years")
            
            with col2:
                pump_type = st.selectbox("Pump Type", ["Tandem t:slim X2", "Omnipod 5", "Medtronic 780G"])
                cgm_type = st.selectbox("CGM Type", ["Dexcom G6", "Dexcom G7", "Guardian 4", "Libre 2"])
                scenario_type = st.selectbox("Primary Challenge", [
                    "dawn_phenomenon", "exercise_management", "post_meal_spikes", 
                    "hypoglycemia_unawareness", "pregnancy_planning", "adolescent_management"
                ])
            
            # Clinical details
            description = st.text_area("Clinical Description", 
                                     "Describe the patient's primary clinical challenge and background")
            clinical_notes = st.text_area("Clinical Notes", 
                                        "Specific observations about glucose patterns or pump issues")
            
            # Initial pump settings
            st.subheader("Initial Pump Settings")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basal Rates (U/hr) - Enter 24 hourly rates:**")
                basal_input = st.text_area("Basal Profile", 
                                         "0.8,0.6,0.5,0.5,0.9,1.2,1.0,0.8,0.7,0.7,0.8,0.9,1.0,0.8,0.7,0.6,0.8,1.1,1.0,0.9,0.8,0.8,0.8,0.8")
                
                breakfast_ic = st.number_input("Breakfast I:C Ratio", value=12)
                lunch_ic = st.number_input("Lunch I:C Ratio", value=15)
                dinner_ic = st.number_input("Dinner I:C Ratio", value=10)
            
            with col2:
                correction_factor = st.number_input("Correction Factor", value=50)
                target_glucose = st.number_input("Target Glucose", value=110)
                
                st.write("**Learning Objectives:**")
                obj1 = st.text_input("Objective 1", "Recognize specific glucose patterns")
                obj2 = st.text_input("Objective 2", "Make appropriate pump adjustments")
                obj3 = st.text_input("Objective 3", "Monitor treatment response")
            
            submit_scenario = st.form_submit_button("Create Scenario")
            
            if submit_scenario:
                try:
                    basal_list = [float(x.strip()) for x in basal_input.split(',')]
                    if len(basal_list) != 24:
                        st.error("Please enter exactly 24 basal rates (one for each hour)")
                    else:
                        new_scenario = {
                            'id': f'custom-{len(st.session_state.custom_scenarios)+1}',
                            'name': name,
                            'age': age,
                            'gender': gender,
                            'mrn': f'CUSTOM-{len(st.session_state.custom_scenarios)+1:03d}',
                            'diabetes_type': 'Type 1',
                            'duration_diabetes': diabetes_duration,
                            'pump_type': pump_type,
                            'cgm_type': cgm_type,
                            'algorithm': 'SmartAdjust' if pump_type == 'Omnipod 5' else 'Control-IQ',
                            'original_settings': {
                                'basal_profile': basal_list,
                                'ic_ratios': {'breakfast': breakfast_ic, 'lunch': lunch_ic, 'dinner': dinner_ic},
                                'correction_factor': correction_factor,
                                'target_glucose': target_glucose
                            },
                            'current_settings': {
                                'basal_profile': basal_list.copy(),
                                'ic_ratios': {'breakfast': breakfast_ic, 'lunch': lunch_ic, 'dinner': dinner_ic},
                                'correction_factor': correction_factor,
                                'target_glucose': target_glucose
                            },
                            'scenario': scenario_type,
                            'description': description,
                            'clinical_notes': clinical_notes,
                            'a1c_trend': [8.0, 7.8, 7.6],
                            'learning_objectives': [obj1, obj2, obj3]
                        }
                        st.session_state.custom_scenarios.append(new_scenario)
                        st.success(f"Created scenario for {name}!")
                except ValueError:
                    st.error("Please enter valid numeric values for basal rates")
    
    with scenario_tabs[1]:
        st.subheader("Manage Custom Scenarios")
        
        if st.session_state.custom_scenarios:
            for scenario in st.session_state.custom_scenarios:
                with st.expander(f"{scenario['name']} - {scenario['scenario']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**Age:** {scenario['age']}")
                        st.write(f"**Pump:** {scenario['pump_type']}")
                        st.write(f"**Challenge:** {scenario['scenario']}")
                    with col2:
                        st.write(f"**Description:** {scenario['description'][:100]}...")
                        st.write(f"**A1C Trend:** {scenario['a1c_trend']}")
                    with col3:
                        if st.button("Delete", key=f"delete_{scenario['id']}"):
                            st.session_state.custom_scenarios.remove(scenario)
                            st.rerun()
        else:
            st.info("No custom scenarios created yet.")
    
    with scenario_tabs[2]:
        st.subheader("Student Learning Analytics")
        st.write("**Platform Usage:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Students", "24")
        with col2:
            st.metric("Scenarios Completed", "156")
        with col3:
            st.metric("Average Time per Case", "18 min")
        
        st.write("*Note: Full analytics would integrate with LMS systems*")

def create_learning_journey(patient):
    """Enhanced learning journey with interactive adjustments"""
    st.markdown(f"# 👤 {patient['name']} - Interactive Pump Management")
    
    # Journey progress
    total_weeks = 12
    progress = st.session_state.current_week / total_weeks
    st.progress(progress)
    st.write(f"Week {st.session_state.current_week + 1} of {total_weeks}")
    
    # Patient scenario description
    st.markdown(f"""
    <div class="info-box">
        <strong>Clinical Scenario:</strong> {patient['description']}<br>
        <strong>Primary Challenge:</strong> {patient['clinical_notes']}<br>
        <strong>Learning Objectives:</strong><br>
    """, unsafe_allow_html=True)
    
    if 'learning_objectives' in patient:
        for obj in patient['learning_objectives']:
            st.markdown(f"• {obj}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Generate glucose data based on current settings
    glucose_df = generate_glucose_data(
        days=7, 
        basal_rates=patient['current_settings']['basal_profile'],
        issues=[patient['scenario']],
        ic_ratios=patient['current_settings']['ic_ratios'],
        correction_factor=patient['current_settings']['correction_factor'],
        week=st.session_state.current_week
    )
    
    # Store current data for comparison
    if not st.session_state.adjustment_made:
        st.session_state.current_glucose_data = glucose_df
    
    # Display glucose plot
    st.subheader("📈 Continuous Glucose Monitor Data")
    fig = create_glucose_plot(glucose_df, f"Week {st.session_state.current_week + 1} - Current Settings")
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display metrics
    st.subheader("📊 Current Glucose Metrics")
    metrics = calculate_glucose_metrics(glucose_df)
    render_glucose_metrics(metrics)
    
    # Interactive adjustment interface
    if st.session_state.current_week < 8:  # Allow adjustments in first 8 weeks
        settings_changed = create_adjustment_interface(patient, st.session_state.current_week)
        
        if settings_changed:
            st.session_state.adjustment_made = True
            st.session_state.learning_stats['adjustments_made'] += 1
            
            # Generate new glucose data with adjusted settings
            new_glucose_df = generate_glucose_data(
                days=7,
                basal_rates=patient['current_settings']['basal_profile'],
                issues=[patient['scenario']],
                ic_ratios=patient['current_settings']['ic_ratios'],
                correction_factor=patient['current_settings']['correction_factor'],
                week=st.session_state.current_week + 1  # Simulate improvement
            )
            
            # Show comparison
            st.subheader("📈 Predicted Glucose Response to Your Adjustments")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Before Adjustments:**")
                old_metrics = calculate_glucose_metrics(st.session_state.current_glucose_data)
                render_glucose_metrics(old_metrics)
            
            with col2:
                st.markdown("**After Adjustments (Predicted):**")
                new_metrics = calculate_glucose_metrics(new_glucose_df)
                render_glucose_metrics(new_metrics)
            
            # Show side-by-side comparison
            fig_comparison = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Before Adjustments', 'After Adjustments (Predicted)')
            )
            
            fig_comparison.add_trace(
                go.Scatter(x=st.session_state.current_glucose_data['timestamp'], 
                          y=st.session_state.current_glucose_data['glucose'],
                          name='Before', line=dict(color='red')),
                row=1, col=1
            )
            
            fig_comparison.add_trace(
                go.Scatter(x=new_glucose_df['timestamp'], y=new_glucose_df['glucose'],
                          name='After', line=dict(color='green')),
                row=2, col=1
            )
            
            # Add target ranges
            for row in [1, 2]:
                fig_comparison.add_hrect(y0=70, y1=180, fillcolor="green", opacity=0.1, 
                                       line_width=0, row=row, col=1)
            
            fig_comparison.update_layout(height=600, title="Glucose Response Comparison")
            fig_comparison.update_yaxes(range=[40, 400])
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Clinical feedback
            tir_improvement = new_metrics['time_in_range'] - old_metrics['time_in_range']
            if tir_improvement > 5:
                st.markdown(f"""
                <div class="success-outcome">
                <strong>Excellent Adjustment!</strong><br>
                Your changes improved Time in Range by {tir_improvement:.1f}%. 
                This demonstrates good clinical reasoning in pump management.
                </div>
                """, unsafe_allow_html=True)
                st.session_state.learning_stats['successful_outcomes'] += 1
            elif tir_improvement > 0:
                st.markdown(f"""
                <div class="success-outcome">
                <strong>Good Adjustment!</strong><br>
                Time in Range improved by {tir_improvement:.1f}%. 
                Consider additional fine-tuning for optimal results.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-outcome">
                <strong>Consider Alternative Approach</strong><br>
                This adjustment may not improve glucose control. 
                Review the patterns and consider different settings.
                </div>
                """, unsafe_allow_html=True)
    
    else:
        st.info("This is the maintenance phase. In clinical practice, continue monitoring and make minor adjustments as needed.")
    
    # Week progression controls
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("➡️ Advance to Next Week", type="primary"):
            if st.session_state.current_week < total_weeks - 1:
                st.session_state.current_week += 1
                st.session_state.adjustment_made = False
                st.rerun()
            else:
                st.success("🎉 Patient journey completed! Excellent work mastering pump management.")
                st.session_state.learning_stats['patients_completed'] += 1
        
        if st.session_state.current_week > 0:
            if st.button("⬅️ Review Previous Week"):
                st.session_state.current_week -= 1
                st.session_state.adjustment_made = False
                st.rerun()

def main():
    """Enhanced main application with professor mode"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>💉 Enhanced Insulin Pump Therapy Platform</h1>
        <h3>Interactive Learning with Real-Time Adjustments</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎯 Learning Dashboard")
    
    # Mode selection
    mode = st.sidebar.radio("Select Mode", ["Student Learning", "Professor Tools"])
    st.session_state.professor_mode = (mode == "Professor Tools")
    
    if st.session_state.professor_mode:
        create_professor_interface()
        return
    
    # Learning progress
    st.sidebar.markdown("### 📈 Your Progress")
    st.sidebar.metric("Patients Completed", st.session_state.learning_stats['patients_completed'])
    st.sidebar.metric("Adjustments Made", st.session_state.learning_stats['adjustments_made'])
    st.sidebar.metric("Successful Outcomes", st.session_state.learning_stats['successful_outcomes'])
    
    # Patient filter options
    st.sidebar.markdown("### 🔍 Patient Filters")
    
    # Combine built-in and custom patients
    all_patients = PUMP_PATIENTS + st.session_state.custom_scenarios
    
    pump_filter = st.sidebar.selectbox(
        "Filter by Pump Type",
        ["All"] + list(set([p['pump_type'] for p in all_patients]))
    )
    scenario_filter = st.sidebar.selectbox(
        "Filter by Clinical Scenario", 
        ["All"] + list(set([p['scenario'].replace('_', ' ').title() for p in all_patients]))
    )
    
    # Filter patients
    filtered_patients = all_patients
    if pump_filter != "All":
        filtered_patients = [p for p in filtered_patients if p['pump_type'] == pump_filter]
    if scenario_filter != "All":
        scenario_key = scenario_filter.lower().replace(' ', '_')
        filtered_patients = [p for p in filtered_patients if p['scenario'] == scenario_key]
    
    # Main content
    if st.session_state.selected_patient is None:
        # Patient selection page
        st.markdown("## 👥 Select a Patient Journey")
        st.markdown("Choose a patient to begin their interactive pump therapy management journey with real-time adjustments and immediate feedback.")
        
        # Overview stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patients", len(all_patients))
        with col2:
            st.metric("Pump Types", len(set([p['pump_type'] for p in all_patients])))
        with col3:
            st.metric("Clinical Scenarios", len(set([p['scenario'] for p in all_patients])))
        with col4:
            st.metric("Interactive Weeks", "12 per patient")
        
        st.markdown("---")
        
        # Patient selection cards
        for patient in filtered_patients:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    render_patient_card(patient)
                    # Show if it's a custom scenario
                    if patient['id'].startswith('custom-'):
                        st.markdown("🏫 **Custom Scenario**")
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Start Journey", key=f"select_{patient['id']}"):
                        st.session_state.selected_patient = patient
                        st.session_state.current_week = 0
                        st.session_state.adjustment_made = False
                        st.rerun()
        
        # Educational content section
        st.markdown("---")
        st.markdown("## 📚 Enhanced Learning Features")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🎯 Interactive Adjustments
            - **Real-Time Settings Changes** - Adjust basal rates, I:C ratios live
            - **Immediate Glucose Response** - See predicted outcomes instantly  
            - **Clinical Validation** - Get feedback on adjustment quality
            - **Safety Guardrails** - Built-in limits prevent unsafe settings
            """)
        
        with col2:
            st.markdown("""
            ### 🔧 Advanced Features
            - **Before/After Comparisons** - Visual glucose improvement tracking
            - **Custom Scenarios** - Professor-created cases for specific learning
            - **Progress Analytics** - Track learning outcomes over time
            - **Clinical Guidelines** - Evidence-based adjustment recommendations
            """)
    
    else:
        # Patient journey page
        patient = st.session_state.selected_patient
        
        # Header with patient info and back button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"## {patient['pump_type']} with {patient['algorithm']}")
        with col2:
            if st.button("← Back to Patients"):
                st.session_state.selected_patient = None
                st.session_state.current_week = 0
                st.session_state.adjustment_made = False
                st.rerun()
        
        # Create the enhanced learning journey
        create_learning_journey(patient)

if __name__ == "__main__":
    main()
