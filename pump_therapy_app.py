"""
Insulin Pump Therapy Educational Platform
Interactive Patient Journey Learning Module

Author: Claude AI Assistant
Purpose: Interactive learning platform for insulin pump management
Focus: Longitudinal patient cases with glucose pattern recognition
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random

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
    .glucose-high { background-color: #ef4444; }
    .glucose-target { background-color: #10b981; }
    .glucose-low { background-color: #f59e0b; }
    
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

# Generate synthetic glucose data
def generate_glucose_data(days=7, basal_rates=None, issues=None):
    """Generate realistic CGM-style glucose data"""
    np.random.seed(42)  # For reproducible data
    
    timestamps = pd.date_range(start='2024-01-01', periods=days*288, freq='5min')
    glucose_values = []
    
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        minute = ts.minute
        
        # Base glucose pattern based on time of day
        if 6 <= hour <= 8:  # Dawn phenomenon
            base_glucose = 140 + np.random.normal(0, 15)
        elif 12 <= hour <= 14:  # Post-lunch
            base_glucose = 160 + np.random.normal(0, 20)
        elif 18 <= hour <= 20:  # Post-dinner
            base_glucose = 150 + np.random.normal(0, 18)
        elif 2 <= hour <= 4:  # Overnight lows
            base_glucose = 95 + np.random.normal(0, 10)
        else:
            base_glucose = 120 + np.random.normal(0, 12)
        
        # Apply specific issues if present
        if issues:
            if 'dawn_phenomenon' in issues and 4 <= hour <= 7:
                base_glucose += 40
            elif 'afternoon_lows' in issues and 14 <= hour <= 16:
                base_glucose -= 30
            elif 'post_meal_spikes' in issues and (hour in [13, 19]):
                base_glucose += 60
            elif 'nocturnal_lows' in issues and 1 <= hour <= 3:
                base_glucose -= 25
        
        # Add some meal-related spikes
        if minute == 0:  # Top of hour meal boluses
            if hour in [7, 12, 18]:  # Meal times
                if random.random() > 0.7:  # 30% chance of missed bolus
                    base_glucose += 80  # High spike
                else:
                    base_glucose += 20  # Normal post-meal rise
        
        # Ensure glucose stays in reasonable bounds
        base_glucose = max(40, min(400, base_glucose))
        glucose_values.append(base_glucose)
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'glucose': glucose_values
    })

# Mock patient data with pump therapy scenarios
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
        'a1c_trend': [7.8, 7.5, 7.2]
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
        'a1c_trend': [6.9, 7.1, 7.3]
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
        'a1c_trend': [8.2, 7.9, 8.1]
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
        'a1c_trend': [6.2, 6.8, 7.0]
    },
    {
        'id': 'pump-005',
        'name': 'Lisa Thompson',
        'age': 31,
        'gender': 'Female',
        'mrn': 'PT005',
        'diabetes_type': 'Type 1',
        'duration_diabetes': '12 years',
        'pump_type': 'Omnipod 5',
        'cgm_type': 'Dexcom G6',
        'algorithm': 'SmartAdjust',
        'current_settings': {
            'basal_profile': [0.7, 0.6, 0.5, 0.5, 0.7, 0.9, 1.0, 0.8, 0.7, 0.8, 0.9, 1.0,
                            1.1, 0.9, 0.8, 0.7, 0.9, 1.2, 1.0, 0.8, 0.7, 0.7, 0.7, 0.7],
            'ic_ratios': {'breakfast': 12, 'lunch': 15, 'dinner': 10},
            'correction_factor': 45,
            'target_glucose': 110
        },
        'scenario': 'pregnancy_planning',
        'description': 'Pre-conception planning requiring tight glucose control',
        'clinical_notes': 'Planning pregnancy in 6 months. A1C goal <6.5%. Needs optimization for tighter control without increased hypoglycemia.',
        'a1c_trend': [7.1, 6.8, 6.9]
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
    """Create interface for making pump adjustments"""
    st.markdown(f"""
    <div class="decision-point">
        <h3>🎯 Week {week + 1} - Time to Make Adjustments</h3>
        <p>Review the glucose patterns and current pump settings. What adjustments would you make?</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current settings display
    with st.expander("📊 Current Pump Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basal Rates (U/hr)")
            basal_df = pd.DataFrame({
                'Hour': range(24),
                'Rate': patient['current_settings']['basal_profile']
            })
            st.bar_chart(basal_df.set_index('Hour'))
        
        with col2:
            st.subheader("Bolus Settings")
            st.write(f"**I:C Ratios:**")
            for meal, ratio in patient['current_settings']['ic_ratios'].items():
                st.write(f"• {meal.title()}: 1:{ratio}")
            st.write(f"**Correction Factor:** 1:{patient['current_settings']['correction_factor']}")
            st.write(f"**Target Glucose:** {patient['current_settings']['target_glucose']} mg/dL")

def create_learning_journey(patient):
    """Create the main learning journey interface"""
    st.markdown(f"# 👤 {patient['name']} - Pump Therapy Journey")
    
    # Journey progress
    total_weeks = 12
    progress = st.session_state.current_week / total_weeks
    st.progress(progress)
    st.write(f"Week {st.session_state.current_week + 1} of {total_weeks}")
    
    # Patient scenario description
    st.markdown(f"""
    <div class="info-box">
        <strong>Clinical Scenario:</strong> {patient['description']}<br>
        <strong>Primary Challenge:</strong> {patient['clinical_notes']}
    </div>
    """, unsafe_allow_html=True)
    
    # Generate glucose data for current week
    issues = [patient['scenario']] if st.session_state.current_week < 4 else []
    glucose_df = generate_glucose_data(days=7, issues=issues)
    
    # Display glucose plot
    st.subheader("📈 Continuous Glucose Monitor Data")
    fig = create_glucose_plot(glucose_df, f"Week {st.session_state.current_week + 1} Glucose Patterns")
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display metrics
    st.subheader("📊 Weekly Glucose Metrics")
    metrics = calculate_glucose_metrics(glucose_df)
    render_glucose_metrics(metrics)
    
    # Pattern recognition section
    st.subheader("🔍 Pattern Recognition")
    
    if patient['scenario'] == 'dawn_phenomenon' and st.session_state.current_week < 4:
        st.markdown("""
        <div class="warning-outcome">
        <strong>Pattern Identified:</strong> Consistent early morning glucose elevation (4-7 AM)
        <br><br>
        <strong>Clinical Insight:</strong> This pattern suggests dawn phenomenon - physiologic rise in glucose due to 
        increased cortisol, growth hormone, and decreased insulin sensitivity in early morning hours.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💡 What adjustment would you make?"):
            st.markdown("""
            <div class="success-outcome">
            <strong>Recommended Adjustment:</strong><br>
            • Increase basal rates from 3-7 AM by 20-30%<br>
            • Consider increasing 3 AM basal from 0.5 → 0.7 U/hr<br>
            • Increase 4-6 AM basal from 0.5-0.9 → 0.7-1.2 U/hr<br><br>
            <strong>Rationale:</strong> Pre-dawn basal increase counteracts hormonal glucose rise
            </div>
            """, unsafe_allow_html=True)
    
    elif patient['scenario'] == 'exercise_management' and st.session_state.current_week < 4:
        st.markdown("""
        <div class="warning-outcome">
        <strong>Pattern Identified:</strong> Consistent hypoglycemia during 4-6 PM period (exercise time)
        <br><br>
        <strong>Clinical Insight:</strong> Exercise increases glucose uptake and insulin sensitivity, 
        leading to hypoglycemia if insulin is not adjusted proactively.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💡 What adjustment would you make?"):
            st.markdown("""
            <div class="success-outcome">
            <strong>Recommended Adjustment:</strong><br>
            • Set temporary basal reduction to 50% starting 1 hour before exercise<br>
            • Enable Exercise Mode on pump (raises target to 140-160 mg/dL)<br>
            • Consider pre-exercise snack if glucose <120 mg/dL<br><br>
            <strong>Rationale:</strong> Proactive insulin reduction prevents exercise-induced hypoglycemia
            </div>
            """, unsafe_allow_html=True)
    
    elif patient['scenario'] == 'post_meal_spikes' and st.session_state.current_week < 4:
        st.markdown("""
        <div class="warning-outcome">
        <strong>Pattern Identified:</strong> Severe post-prandial glucose spikes (>250 mg/dL) 1-2 hours after meals
        <br><br>
        <strong>Clinical Insight:</strong> Inadequate insulin-to-carb ratios or poor bolus timing leading 
        to insufficient mealtime insulin coverage.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💡 What adjustment would you make?"):
            st.markdown("""
            <div class="success-outcome">
            <strong>Recommended Adjustment:</strong><br>
            • Strengthen I:C ratios - reduce from current values by 20%<br>
            • Breakfast: 1:15 → 1:12, Lunch: 1:18 → 1:15, Dinner: 1:12 → 1:10<br>
            • Educate on pre-bolusing 15-20 minutes before meals<br>
            • Consider extended bolus for high-fat meals<br><br>
            <strong>Rationale:</strong> More aggressive mealtime insulin dosing to match carb absorption
            </div>
            """, unsafe_allow_html=True)
    
    # Week progression controls
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("➡️ Advance to Next Week", type="primary"):
            if st.session_state.current_week < total_weeks - 1:
                st.session_state.current_week += 1
                st.session_state.learning_stats['adjustments_made'] += 1
                st.rerun()
            else:
                st.success("🎉 Patient journey completed! Great work learning pump management.")
                st.session_state.learning_stats['patients_completed'] += 1
        
        if st.session_state.current_week > 0:
            if st.button("⬅️ Review Previous Week"):
                st.session_state.current_week -= 1
                st.rerun()

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>💉 Insulin Pump Therapy Learning Platform</h1>
        <h3>Interactive Patient Journeys in Diabetes Technology</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎯 Learning Dashboard")
    
    # Learning progress
    st.sidebar.markdown("### 📈 Your Progress")
    st.sidebar.metric("Patients Completed", st.session_state.learning_stats['patients_completed'])
    st.sidebar.metric("Adjustments Made", st.session_state.learning_stats['adjustments_made'])
    st.sidebar.metric("Successful Outcomes", st.session_state.learning_stats['successful_outcomes'])
    
    # Patient filter options
    st.sidebar.markdown("### 🔍 Patient Filters")
    pump_filter = st.sidebar.selectbox(
        "Filter by Pump Type",
        ["All"] + list(set([p['pump_type'] for p in PUMP_PATIENTS]))
    )
    scenario_filter = st.sidebar.selectbox(
        "Filter by Clinical Scenario", 
        ["All"] + list(set([p['scenario'].replace('_', ' ').title() for p in PUMP_PATIENTS]))
    )
    
    # Filter patients
    filtered_patients = PUMP_PATIENTS
    if pump_filter != "All":
        filtered_patients = [p for p in filtered_patients if p['pump_type'] == pump_filter]
    if scenario_filter != "All":
        scenario_key = scenario_filter.lower().replace(' ', '_')
        filtered_patients = [p for p in filtered_patients if p['scenario'] == scenario_key]
    
    # Main content
    if st.session_state.selected_patient is None:
        # Patient selection page
        st.markdown("## 👥 Select a Patient Journey")
        st.markdown("Choose a patient to begin their longitudinal pump therapy management journey. Each case focuses on different clinical challenges and pump optimization strategies.")
        
        # Overview stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patients", len(PUMP_PATIENTS))
        with col2:
            st.metric("Pump Types", len(set([p['pump_type'] for p in PUMP_PATIENTS])))
        with col3:
            st.metric("Clinical Scenarios", len(set([p['scenario'] for p in PUMP_PATIENTS])))
        with col4:
            st.metric("Learning Weeks", "12 per patient")
        
        st.markdown("---")
        
        # Patient selection cards
        for patient in filtered_patients:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    render_patient_card(patient)
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                    if st.button("Start Journey", key=f"select_{patient['id']}"):
                        st.session_state.selected_patient = patient
                        st.session_state.current_week = 0
                        st.rerun()
        
        # Educational content section
        st.markdown("---")
        st.markdown("## 📚 Learning Objectives")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🎯 Core Competencies
            - **Glucose Pattern Recognition** - Identify dawn phenomenon, post-meal spikes, exercise lows
            - **Pump Setting Optimization** - Adjust basal rates, I:C ratios, correction factors
            - **Algorithm Integration** - Understand hybrid closed-loop system behaviors
            - **Safety Protocols** - Recognize when to intervene vs. let automation work
            """)
        
        with col2:
            st.markdown("""
            ### 🔧 Technical Skills
            - **CGM Data Interpretation** - Time in range, variability, trend analysis
            - **Insulin Dose Calculations** - Basal testing, carb counting validation
            - **Troubleshooting** - Site issues, occlusions, algorithm exits
            - **Patient Education** - Teaching self-management and adjustment principles
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
                st.rerun()
        
        # Create the learning journey
        create_learning_journey(patient)

if __name__ == "__main__":
    main()
