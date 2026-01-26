"""
Databricks App for Payment Approval Acceleration Demo

Interactive dashboard application showcasing real-time approval optimization,
decline analysis, and smart retry recommendations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from databricks import sql
import os
from datetime import datetime, timedelta
import yaml

# Page configuration
st.set_page_config(
    page_title="Payment Approval Acceleration",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
@st.cache_resource
def load_config():
    with open("../config/app_config.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_config()

# Database connection
@st.cache_resource
def get_db_connection():
    return sql.connect(
        server_hostname=os.getenv("DATABRICKS_HOST"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-metric {
        color: #28a745;
        font-size: 2rem;
        font-weight: bold;
    }
    .warning-metric {
        color: #ffc107;
        font-size: 2rem;
        font-weight: bold;
    }
    .danger-metric {
        color: #dc3545;
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">💳 Payment Approval Acceleration Platform</div>', unsafe_allow_html=True)
st.markdown("**Powered by Azure Databricks** | Real-time decisioning, ML-driven optimization, and actionable insights")

# Sidebar
with st.sidebar:
    st.image("https://www.databricks.com/wp-content/uploads/2021/06/db-nav-logo.svg", width=200)
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Overview", "🎯 Smart Checkout", "📉 Decline Analysis", "🔄 Smart Retry", "⚙️ Settings"]
    )
    
    st.markdown("---")
    st.markdown("### Filters")
    
    date_range = st.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=7), datetime.now()),
        max_value=datetime.now()
    )
    
    geography_filter = st.multiselect(
        "Geography",
        ["US", "UK", "EU", "LATAM", "APAC"],
        default=["US", "UK", "EU", "LATAM", "APAC"]
    )
    
    st.markdown("---")
    st.markdown("### Data Refresh")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Data refreshed!")

# Helper functions
@st.cache_data(ttl=300)
def get_overview_metrics():
    """Get key metrics for overview page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total transactions
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
            AVG(amount) as avg_amount,
            AVG(processing_time_ms) as avg_processing_time
        FROM silver_transactions
        WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL 7 DAYS
    """)
    
    result = cursor.fetchone()
    cursor.close()
    
    return {
        "total_transactions": result[0],
        "approved_transactions": result[1],
        "approval_rate": result[1] / result[0] if result[0] > 0 else 0,
        "avg_amount": result[2],
        "avg_processing_time": result[3]
    }

@st.cache_data(ttl=300)
def get_approval_trends():
    """Get approval rate trends"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as total,
            SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved
        FROM silver_transactions
        WHERE DATE(timestamp) >= CURRENT_DATE - INTERVAL 30 DAYS
        GROUP BY DATE(timestamp)
        ORDER BY date
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    df = pd.DataFrame(results, columns=['date', 'total', 'approved'])
    df['approval_rate'] = df['approved'] / df['total']
    
    return df

@st.cache_data(ttl=300)
def get_decline_reasons():
    """Get decline reason distribution"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            decline_reason_description,
            COUNT(*) as count
        FROM silver_transactions
        WHERE is_approved = FALSE
        AND DATE(timestamp) >= CURRENT_DATE - INTERVAL 7 DAYS
        GROUP BY decline_reason_description
        ORDER BY count DESC
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    return pd.DataFrame(results, columns=['reason', 'count'])

# Page: Overview
if page == "📊 Overview":
    st.header("Overview Dashboard")
    
    # Key Metrics
    metrics = get_overview_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Transactions",
            value=f"{metrics['total_transactions']:,}",
            delta="+12.5% vs last week"
        )
    
    with col2:
        approval_rate = metrics['approval_rate']
        st.metric(
            label="Approval Rate",
            value=f"{approval_rate:.1%}",
            delta=f"+{(approval_rate - 0.85):.1%} vs baseline"
        )
    
    with col3:
        st.metric(
            label="Avg Transaction",
            value=f"${metrics['avg_amount']:.2f}",
            delta="+$5.23"
        )
    
    with col4:
        st.metric(
            label="Avg Processing Time",
            value=f"{metrics['avg_processing_time']:.0f}ms",
            delta="-15ms"
        )
    
    st.markdown("---")
    
    # Approval Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Approval Rate Trend (30 Days)")
        trends_df = get_approval_trends()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trends_df['date'],
            y=trends_df['approval_rate'],
            mode='lines+markers',
            name='Approval Rate',
            line=dict(color='#1f77b4', width=3)
        ))
        fig.add_hline(y=0.85, line_dash="dash", line_color="red", 
                     annotation_text="Baseline (85%)")
        fig.update_layout(
            yaxis_title="Approval Rate",
            xaxis_title="Date",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Decline Reasons")
        decline_df = get_decline_reasons()
        
        fig = px.bar(
            decline_df,
            x='count',
            y='reason',
            orientation='h',
            color='count',
            color_continuous_scale='Reds'
        )
        fig.update_layout(
            xaxis_title="Number of Declines",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Geography Performance
    st.subheader("Performance by Geography")
    
    # Mock data for demo
    geo_data = pd.DataFrame({
        'geography': ['US', 'UK', 'EU', 'LATAM', 'APAC'],
        'transactions': [150000, 50000, 75000, 40000, 35000],
        'approval_rate': [0.89, 0.87, 0.86, 0.82, 0.85],
        'avg_amount': [125.50, 98.30, 110.20, 85.40, 95.60]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            geo_data,
            x='geography',
            y='approval_rate',
            color='approval_rate',
            color_continuous_scale='RdYlGn',
            range_color=[0.75, 0.95]
        )
        fig.update_layout(
            title="Approval Rate by Geography",
            yaxis_title="Approval Rate",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            geo_data,
            x='transactions',
            y='approval_rate',
            size='avg_amount',
            color='geography',
            hover_data=['avg_amount']
        )
        fig.update_layout(
            title="Volume vs Approval Rate",
            xaxis_title="Transaction Volume",
            yaxis_title="Approval Rate",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

# Page: Smart Checkout
elif page == "🎯 Smart Checkout":
    st.header("Smart Checkout Optimization")
    
    st.markdown("""
    Smart Checkout uses ML models to dynamically select optimal payment solutions
    for each transaction, maximizing approval rates while maintaining security.
    """)
    
    # Payment Solutions Performance
    st.subheader("Payment Solutions Performance")
    
    solutions_data = pd.DataFrame({
        'solution': ['NetworkToken', '3DS', 'IDPay', 'Passkey', 'Antifraud', 'DataShareOnly'],
        'approval_rate': [0.95, 0.91, 0.93, 0.96, 0.88, 0.85],
        'usage_count': [45000, 120000, 35000, 15000, 80000, 50000],
        'cost_per_txn': [0.25, 0.15, 0.20, 0.30, 0.10, 0.05],
        'approval_lift': [0.15, 0.05, 0.12, 0.20, 0.08, 0.03]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            solutions_data,
            x='solution',
            y='approval_rate',
            color='approval_lift',
            color_continuous_scale='Greens',
            title="Approval Rate by Payment Solution"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            solutions_data,
            x='cost_per_txn',
            y='approval_rate',
            size='usage_count',
            color='solution',
            title="Cost vs Approval Rate"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # ROI Calculator
    st.subheader("ROI Calculator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        monthly_volume = st.number_input(
            "Monthly Transaction Volume",
            min_value=1000,
            max_value=10000000,
            value=1000000,
            step=10000
        )
    
    with col2:
        avg_txn_value = st.number_input(
            "Average Transaction Value ($)",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=10.0
        )
    
    with col3:
        baseline_approval = st.slider(
            "Baseline Approval Rate (%)",
            min_value=70,
            max_value=95,
            value=85
        ) / 100
    
    # Calculate ROI
    improvement = 0.08  # 8% improvement
    new_approval_rate = min(0.99, baseline_approval + improvement)
    additional_approvals = monthly_volume * improvement
    additional_revenue = additional_approvals * avg_txn_value
    annual_revenue = additional_revenue * 12
    
    st.markdown("### Projected Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**New Approval Rate**")
        st.markdown(f'<div class="success-metric">{new_approval_rate:.1%}</div>', unsafe_allow_html=True)
        st.markdown(f"+{improvement:.1%} improvement")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**Additional Approvals/Month**")
        st.markdown(f'<div class="success-metric">{additional_approvals:,.0f}</div>', unsafe_allow_html=True)
        st.markdown(f"From {monthly_volume:,} total")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**Monthly Revenue Impact**")
        st.markdown(f'<div class="success-metric">${additional_revenue:,.0f}</div>', unsafe_allow_html=True)
        st.markdown("Additional revenue")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("**Annual Revenue Impact**")
        st.markdown(f'<div class="success-metric">${annual_revenue:,.0f}</div>', unsafe_allow_html=True)
        st.markdown("Projected annually")
        st.markdown('</div>', unsafe_allow_html=True)

# Page: Decline Analysis
elif page == "📉 Decline Analysis":
    st.header("Decline Analysis & Insights")
    
    st.markdown("""
    Transform decline signals into actionable insights with real-time analysis
    of decline patterns, root causes, and improvement opportunities.
    """)
    
    # Decline Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Declines (7d)", "75,234", "-5.2%")
    
    with col2:
        st.metric("Decline Rate", "14.8%", "-1.2%")
    
    with col3:
        st.metric("Recoverable Declines", "52,164", "69.3%")
    
    st.markdown("---")
    
    # Root Cause Analysis
    st.subheader("Root Cause Analysis")
    
    root_causes = pd.DataFrame({
        'category': ['Insufficient Funds', 'Fraud Suspected', 'Issuer Policy', 
                    'Expired Card', 'Limit Exceeded', 'Other'],
        'count': [26500, 12000, 15000, 8500, 7234, 6000],
        'recoverable_pct': [0.65, 0.05, 0.35, 0.75, 0.55, 0.40]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(
            root_causes,
            values='count',
            names='category',
            title="Decline Distribution by Root Cause"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            root_causes,
            x='category',
            y='recoverable_pct',
            color='recoverable_pct',
            color_continuous_scale='RdYlGn',
            title="Recovery Potential by Category"
        )
        fig.update_layout(height=400, yaxis_title="Recoverable %")
        st.plotly_chart(fig, use_container_width=True)
    
    # Actionable Recommendations
    st.subheader("Actionable Recommendations")
    
    recommendations = [
        {
            "priority": "🔴 HIGH",
            "category": "Insufficient Funds",
            "action": "Implement Smart Retry with 24-72 hour delay",
            "impact": "30-40% recovery rate",
            "affected": "26,500 transactions"
        },
        {
            "priority": "🔴 HIGH",
            "category": "Issuer Policy",
            "action": "Engage with issuers for policy clarification; implement smart routing",
            "impact": "10-15% improvement",
            "affected": "15,000 transactions"
        },
        {
            "priority": "🟡 MEDIUM",
            "category": "Expired Card",
            "action": "Implement Account Updater service",
            "impact": "70-80% recovery rate",
            "affected": "8,500 transactions"
        },
        {
            "priority": "🟢 LOW",
            "category": "Fraud Suspected",
            "action": "Review fraud detection thresholds; reduce false positives",
            "impact": "15-20% reduction in false positives",
            "affected": "12,000 transactions"
        }
    ]
    
    for rec in recommendations:
        with st.expander(f"{rec['priority']} - {rec['category']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Action:** {rec['action']}")
            with col2:
                st.markdown(f"**Expected Impact:** {rec['impact']}")
            with col3:
                st.markdown(f"**Affected:** {rec['affected']}")

# Page: Smart Retry
elif page == "🔄 Smart Retry":
    st.header("Smart Retry Optimization")
    
    st.markdown("""
    Intelligent retry logic that learns optimal timing and conditions for retrying
    declined transactions, maximizing recovery while minimizing costs.
    """)
    
    # Retry Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Retry Success Rate", "37.5%", "+12.3%")
    
    with col2:
        st.metric("Avg Retry Delay", "28.5 hrs", "-8.5 hrs")
    
    with col3:
        st.metric("Recovered Revenue (7d)", "$1.2M", "+$350K")
    
    with col4:
        st.metric("Blocked Low-Prob Retries", "12,450", "Saved costs")
    
    st.markdown("---")
    
    # Optimal Retry Timing
    st.subheader("Optimal Retry Timing by Decline Reason")
    
    timing_data = pd.DataFrame({
        'decline_reason': ['Insufficient Funds', 'Limit Exceeded', 'Issuer Policy', 
                          'Do Not Honor', 'Invalid Transaction'],
        '1h': [0.15, 0.10, 0.08, 0.12, 0.05],
        '6h': [0.25, 0.18, 0.15, 0.20, 0.10],
        '24h': [0.65, 0.45, 0.35, 0.38, 0.25],
        '48h': [0.55, 0.40, 0.30, 0.32, 0.20],
        '72h': [0.40, 0.35, 0.25, 0.28, 0.18]
    })
    
    fig = go.Figure()
    
    for delay in ['1h', '6h', '24h', '48h', '72h']:
        fig.add_trace(go.Bar(
            name=delay,
            x=timing_data['decline_reason'],
            y=timing_data[delay]
        ))
    
    fig.update_layout(
        barmode='group',
        title="Success Rate by Retry Delay",
        xaxis_title="Decline Reason",
        yaxis_title="Success Rate",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Retry Decision Simulator
    st.subheader("Retry Decision Simulator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        decline_reason = st.selectbox(
            "Decline Reason",
            ["Insufficient Funds", "Fraud Suspected", "Expired Card", 
             "Limit Exceeded", "Issuer Policy"]
        )
    
    with col2:
        retry_attempt = st.number_input(
            "Retry Attempt #",
            min_value=0,
            max_value=5,
            value=0
        )
    
    with col3:
        hours_since_decline = st.number_input(
            "Hours Since Decline",
            min_value=0,
            max_value=168,
            value=24
        )
    
    # Simulate decision
    if st.button("Get Retry Recommendation"):
        # Mock recommendation logic
        if decline_reason == "Fraud Suspected":
            st.error("❌ **Do Not Retry** - Fraud-related decline")
        elif decline_reason == "Expired Card":
            st.warning("⚠️ **Conditional Retry** - Requires card update")
        elif retry_attempt >= 3:
            st.error("❌ **Do Not Retry** - Maximum attempts reached")
        elif decline_reason == "Insufficient Funds" and hours_since_decline >= 24:
            st.success("✅ **Retry Recommended** - Optimal window (65% success rate)")
            st.info(f"Recommended delay: 24 hours from original decline")
        else:
            st.info("⏳ **Wait** - Retry in {24 - hours_since_decline} hours for optimal results")

# Page: Settings
elif page == "⚙️ Settings":
    st.header("Settings & Configuration")
    
    st.subheader("Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Approval Predictor Model**")
        st.text("Version: v1.2.3")
        st.text("Status: Production")
        st.text("Last Updated: 2026-01-20")
        if st.button("Deploy New Version"):
            st.success("Model deployment initiated")
    
    with col2:
        st.markdown("**Smart Retry Model**")
        st.text("Version: v1.1.0")
        st.text("Status: Production")
        st.text("Last Updated: 2026-01-18")
        if st.button("Rollback Version"):
            st.warning("Rollback initiated")
    
    st.markdown("---")
    
    st.subheader("Thresholds & Rules")
    
    fraud_threshold = st.slider(
        "Fraud Score Threshold",
        min_value=0,
        max_value=100,
        value=50
    )
    
    retry_threshold = st.slider(
        "Retry Success Probability Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05
    )
    
    max_retry_attempts = st.number_input(
        "Maximum Retry Attempts",
        min_value=1,
        max_value=10,
        value=3
    )
    
    if st.button("Save Configuration"):
        st.success("Configuration saved successfully")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Payment Approval Acceleration Platform | Powered by Azure Databricks</p>
    <p>© 2026 | Built with Databricks Apps, MLflow, and Delta Lake</p>
</div>
""", unsafe_allow_html=True)
