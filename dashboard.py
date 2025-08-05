import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

def show():
    st.set_page_config(layout="wide")

    st.markdown("""
        <style>
            body {
                background-color: #121212;
                color: #fff;
            }
            .block-container {
                padding: 2rem 3rem;
            }
            .card {
                background: linear-gradient(to bottom right, #222, #333);
                padding: 1.5rem;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                text-align: left;
                color: white;
            }
            .card h2 {
                font-size: 2rem;
                margin-bottom: 0.3rem;
                color: #fff;
            }
            .card span {
                font-size: 1rem;
                color: #bbb;
            }
            .stat-title {
                color: #bbb;
                font-size: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Database connection
    conn = psycopg2.connect(
        dbname="Underwritter",
        user="postgres",
        password="United2025",
        host="localhost",
        port="5432"
    )

    df = pd.read_sql("SELECT * FROM vehicle_risk", conn)

    if df.empty:
        st.warning("No data found. Please calculate risk profiles first.")
        return

    # KPIs
    total_profiles = len(df)
    avg_premium = round(df['premium_rate'].mean(), 2)
    unique_makes = df['make_name'].nunique()

    st.markdown("## 🛡️ Insurance Coverage Summary")
    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
        <div class="card">
            <h2>$10 L</h2>
            <span>Health Insurance (1)</span>
        </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
        <div class="card">
            <h2>$8 L</h2>
            <span>Vehicle Insurance (4)</span>
        </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
        <div class="card">
            <h2>$45 L</h2>
            <span>Wealth Insurance (8)</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==============================
    # 📊 Policy Portfolio Stats Graph (Dual-Line Area)
    # ==============================

    st.markdown("## 📊 Policy Portfolio Stats")

    # Replace this with real aggregated data if available
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    earning = [10000, 15000, 30000, 18000, 12000, 7000]
    investment = [5000, 10000, 18000, 12000, 8000, 4000]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months,
        y=earning,
        name='Earning',
        mode='lines+markers',
        line=dict(color='mediumpurple', width=3),
        fill='tozeroy',
        marker=dict(size=8)
    ))

    fig.add_trace(go.Scatter(
        x=months,
        y=investment,
        name='Investment',
        mode='lines+markers',
        line=dict(color='gold', width=3),
        fill='tozeroy',
        marker=dict(size=8)
    ))

    fig.add_annotation(
        x='Mar',
        y=30000,
        text='30L',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        font=dict(size=16, color='white'),
        bgcolor='purple',
        opacity=0.9
    )

    fig.update_layout(
        title='Policy Portfolio Stats',
        xaxis_title='Month',
        yaxis_title='Amount',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # =============================
    # Risk Level Pie Chart
    # =============================
    st.markdown("## 📌 Risk & Premium Stats")

    col4, col5 = st.columns(2)

    risk_pie = px.pie(
        df,
        names='risk_level',
        title='Risk Level Distribution',
        hole=0.5,
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    risk_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    col4.plotly_chart(risk_pie, use_container_width=True)

    premium_make = df.groupby('make_name')['premium_rate'].mean().reset_index()
    premium_bar = px.bar(
        premium_make,
        x='make_name',
        y='premium_rate',
        title='Average Premium Rate by Make',
        color='premium_rate',
        color_continuous_scale='thermal'
    )
    premium_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    col5.plotly_chart(premium_bar, use_container_width=True)

    # =============================
    # Filtered Line Chart: Premium by Make & Year
    # =============================

    st.markdown("## 🔍 Premium Rate by Make & Model Year")
    selected_makes = st.multiselect("Select Make(s):", df['make_name'].unique())

    if selected_makes:
        filtered_df = df[df['make_name'].isin(selected_makes)]
        make_model_avg = (
            filtered_df.groupby(['make_name', 'model_year'])['premium_rate']
            .mean().reset_index()
        )
        make_model_chart = px.line(
            make_model_avg,
            x='model_year',
            y='premium_rate',
            color='make_name',
            title='Trend by Make & Year',
            markers=True
        )
        make_model_chart.update_traces(line=dict(width=2), marker=dict(size=6))
        make_model_chart.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(make_model_chart, use_container_width=True)
    else:
        st.info("Please select a make to view the chart.")

    # Close DB
    conn.close()
