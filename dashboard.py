import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from pathlib import Path

def show():
    st.title("📊 Underwriting Dashboard")
    st.markdown("#### Get a clear view of your risk profiles & premium distribution")

    # --- DB ---
    conn = psycopg2.connect(
        dbname="Underwritter",
        user="postgres",
        password="United2025",
        host="localhost",
        port="5432"
    )

    df = pd.read_sql("SELECT * FROM vehicle_risk", conn)

    if df.empty:
        st.warning("No data yet. Calculate risk profiles first!")
        return

    total_profiles = len(df)
    avg_premium = round(df['premium_rate'].mean(), 2) if not df['premium_rate'].isnull().all() else 0
    unique_makes = df['make_name'].nunique()

    # --- Stylish Cards ---
    card_html = f"""
        <style>
        .card {{
            background: #f5f5f5;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            text-align: center;
            margin-bottom: 15px;
        }}
        .card h2 {{
            margin: 0;
            font-size: 2em;
            color: #333;
        }}
        .card p {{
            margin: 5px 0 0 0;
            color: #666;
            font-size: 1em;
        }}
        </style>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"<div class='card'><h2>{total_profiles}</h2><p>Total Risk Profiles</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h2>{avg_premium} %</h2><p>Average Premium Rate</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h2>{unique_makes}</h2><p>Unique Makes</p></div>", unsafe_allow_html=True)

    st.divider()

    # --- Risk Level Pie ---
    risk_pie = px.pie(
        df,
        names='risk_level',
        title='Risk Level Share',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    risk_pie.update_traces(textinfo='percent+label')

    # --- Premium by Make (Bar) ---
    premium_make = df.groupby('make_name')['premium_rate'].mean().reset_index()
    premium_bar = px.bar(
        premium_make,
        x='make_name',
        y='premium_rate',
        title='Avg Premium Rate by Make',
        color='premium_rate',
        color_continuous_scale='blues'
    )

    # --- Premium Trend ---
    premium_trend = df.groupby('model_year')['premium_rate'].mean().reset_index()
    premium_line = px.line(
        premium_trend,
        x='model_year',
        y='premium_rate',
        title='Premium Rate Trend Over Years',
        markers=True,
        line_shape='spline'
    )

    premium_line.update_traces(line=dict(width=3), marker=dict(size=8))

    # --- Layout 2x2 ---
    col4, col5 = st.columns(2)
    col4.plotly_chart(risk_pie, use_container_width=True)
    col5.plotly_chart(premium_bar, use_container_width=True)

    st.plotly_chart(premium_line, use_container_width=True)

    conn.close()
