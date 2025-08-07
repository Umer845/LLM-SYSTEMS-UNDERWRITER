import streamlit as st
import dashboard
import pandas as pd
import qa
from pathlib import Path
from utils.db_utils import insert_vehicle_inspection
from utils.db_utils import get_vehicle_claims, insert_vehicle_risk
from datetime import datetime
from PyPDF2 import PdfReader
from utils.db_utils import (
    get_latest_suminsured_netpremium,
    get_tracker_id,
    get_risk_level,
    update_vehicle_risk_premium
)


# ---- PAGE CONFIG ----
st.set_page_config(page_title="Insurance Underwriting System", layout="wide")

# ---- SESSION STATE ----
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

st.markdown("""
<style>
.st-emotion-cache-umot6g {
    display: inline-flex;
    -webkit-box-align: center;
    align-items: center;
    -webkit-box-pack: center;
    justify-content: center;
    font-weight: 400;
    padding: 8px 12px;
    border-radius: 0.5rem;
    min-height: 3rem;
    margin: 0px;
    line-height: 1.6;
    text-transform: none;
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    width: 200px;
    cursor: pointer;
    user-select: none;
    background-color: rgb(43, 44, 54);
    border: 1px solid rgba(250, 250, 250, 0.2);
}
.st-emotion-cache-umot6g:hover{
border:1px solid #14C76D;
color: #14C76D;
background:transparent;
}
.st-emotion-cache-umot6g:active {
    color: #fff;
    border-color: #14C76D;
    background-color: #14C76D;
}
.st-emotion-cache-umot6g:focus:not(:active) {
    border-color: #14C76D;
    color: #14C76D;
}

.st-emotion-cache-9gx57n {
    display: flex;
    flex-flow: row;
    -webkit-box-align: center;
    align-items: center;
    height: 3rem;
    border-width: 1px;
    border-style: solid;
    border-color: none;
    transition-duration: 200ms;
    transition-property: border;
    transition-timing-function: cubic-bezier(0.2, 0.8, 0.4, 1);
    border-radius: 0.5rem;
    overflow: hidden;
}

.st-br {
    line-height: 2.4;
}
.st-dk {
    line-height: 2.4;
}
.st-b3 {
    margin-top: 0.74rem;
}
.st-c3{
height:3rem;
}
.st-emotion-cache-z8vbw2:hover {
    border-color: #14C76D;
    color: #14C76D;
}
.st-emotion-cache-z8vbw2 {
    display: inline-flex;
    -webkit-box-align: center;
    align-items: center;
    -webkit-box-pack: center;
    justify-content: center;
    font-weight: 400;
    padding: 8px 12px;
    border-radius: 0.5rem;
    min-height: 2.5rem;
    margin: 0px;
    line-height: 1.6;
    text-transform: none;
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    width: auto;
    cursor: pointer;
    user-select: none;
    background-color: rgb(19, 23, 32);
    border: 1px solid rgba(250, 250, 250, 0.2);
}
.st-cj .st-ci .st-ch .st-cc:active{
    border: #14C76D;
}
</style>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
with st.sidebar:
    st.image("https://i.postimg.cc/W4ZNtNxP/usti-logo-1.png")
    st.markdown("Welcome, ")

    st.sidebar.title("Navigation")
    if st.button("Dashboard"):
        st.session_state.page = "Dashboard"
    if st.button("Upload Files"):
        st.session_state.page = "Upload Files"
    if st.button("Risk Calculation"):
        st.session_state.page = "Risk Profile"
    if st.button("Premium Calculation"):
        st.session_state.page = "Premium Calculation"
    if st.button("QA"):
        st.session_state.page = "QA"
    if st.button("Logout"):
        st.session_state.page = "Logout"

# ---- HEADER ----
header_html = Path("templates/header.html").read_text(encoding="utf-8")
st.markdown(header_html, unsafe_allow_html=True)

# ---- PAGES ----

# ✅✅✅ Properly call dashboard when page is Dashboard
if st.session_state.page == "Dashboard":
    dashboard.show()

elif st.session_state.page == "Upload Files":
    st.subheader("Upload Vehicle Data")

    file_type = st.radio("Select file type", ["Excel (.xlsx)", "PDF (.pdf)"])
    uploaded_file = st.file_uploader("Choose file", type=['xlsx', 'pdf'])

    if uploaded_file is not None:
        if file_type == "Excel (.xlsx)":
            df = pd.read_excel(uploaded_file)
            st.write(df)

            if st.button("Save Excel to DB", key="save_excel"):
                try:
                    insert_vehicle_inspection(df, st.session_state.get('user_id', 1))  # fallback id
                    st.success("✅ Excel data inserted into `vehicle_inspection`!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        elif file_type == "PDF (.pdf)":
            pdf = PdfReader(uploaded_file)
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            st.session_state['pdf_context'] = text
            st.success("✅ PDF uploaded and context saved for Q&A!")

    # ================================
    # 🚩 RISK PROFILE PAGE
    # ================================

elif st.session_state.page == "Risk Profile":
    st.subheader("Calculate Risk Profile")

    driver_age = st.number_input("Driver Age", min_value=18, max_value=100)
    make_name = st.text_input("Make Name", value="Proton")
    sub_make_name = st.text_input("Sub Make Name", value="Saga")
    model_year = st.number_input("Model Year", min_value=2020, max_value=datetime.now().year)

    if st.button("Calculate Risk", key="calc_risk"):
        current_year = datetime.now().year

        if model_year < current_year - 5:
            st.warning(f"⚠️ Only vehicles up to 5 years old can have their risk profile calculated! Please enter a model year >= {current_year - 5}.")
        else:
            row = get_vehicle_claims(make_name, sub_make_name, model_year)

            if row and row[0] is not None and row[1] is not None:
                avg_no_of_claims, avg_vehicle_capacity = row

                # ---- Calculate scores ----
                if driver_age < 25:
                    age_score = 1.0
                elif 25 <= driver_age <= 35:
                    age_score = 0.6
                elif 36 <= driver_age <= 55:
                    age_score = 0.4
                else:
                    age_score = 1.0

                if avg_vehicle_capacity <= 1000:
                    cap_score = 0.4
                elif 1001 <= avg_vehicle_capacity <= 1600:
                    cap_score = 0.6
                elif 1601 <= avg_vehicle_capacity <= 2000:
                    cap_score = 0.8
                else:
                    cap_score = 1.0

                if avg_no_of_claims < 2:
                    claim_score = 0.4
                elif 2 <= avg_no_of_claims <= 3:
                    claim_score = 0.6
                elif 4 <= avg_no_of_claims <= 5:
                    claim_score = 0.8
                else:
                    claim_score = 1.0

                total_score = age_score + cap_score + claim_score

                if total_score <= 1.8:
                    risk_level = "Low"
                elif 1.8 < total_score <= 2.4:
                    risk_level = "Low to Moderate"
                elif 2.4 < total_score < 3:
                    risk_level = "Moderate to High"
                else:
                    risk_level = "High"

                bg_color = {
                    "Low": "#32da32",
                    "Low to Moderate": "#d4c926",
                    "Moderate to High": "#26b4d4",
                    "High": "#dd2c2c"
                }[risk_level]

                st.info(f"""
                **Fetched Data:**
                - Vehicle Capacity: {avg_vehicle_capacity:.2f}
                - Average Number of Claims: {avg_no_of_claims:.2f}

                **Risk Scores:**
                - Age: {age_score}
                - Capacity: {cap_score}
                - Claims: {claim_score}

                **Total Score:** {total_score:.2f}
                """)

                st.markdown(f"""
                    <div style="background-color: {bg_color}; color: white; padding: 12px; border-radius: 6px;">
                        ✅ <b>Risk Level:</b> {risk_level}
                    </div>
                """, unsafe_allow_html=True)

                risk_id = insert_vehicle_risk(
                    user_id=st.session_state.get('user_id', 1),  # fallback ID for dev
                    driver_age=driver_age,
                    make_name=make_name,
                    sub_make_name=sub_make_name,
                    model_year=model_year,
                    capacity=avg_vehicle_capacity,
                    num_claims=avg_no_of_claims,
                    risk_level=risk_level
                )

                st.session_state['risk_id'] = risk_id
                st.success("✅ Risk profile saved!")

            else:
                st.error("No matching data found with claims > 0!")

    # ================================
    # 🚩 Premium Calculation
    # ================================

elif st.session_state.page == "Premium Calculation":
    st.subheader("Calculate Premium")

    if 'risk_id' not in st.session_state:
        st.warning("⚠️ Please calculate risk profile first.")
    else:
        make_name = st.text_input("Make Name", key="premium_make")
        sub_make_name = st.text_input("Sub Make Name", key="premium_sub_make")
        model_year = st.number_input("Model Year", min_value=2020, max_value=2035, key="premium_year")

        if st.button("Calculate Premium", key="calc_premium"):
            if model_year == 2025:
                row = get_latest_suminsured_netpremium(make_name, sub_make_name, 2024)
                if row and row[0] and row[1]:
                    suminsured, netpremium = row

                    base_premium_rate = (netpremium / suminsured) * 100

                    risk_level = get_risk_level(st.session_state['risk_id'])

                    if risk_level == "Low":
                        base_premium_rate *= 1.10
                    elif risk_level == "Low to Moderate":
                        base_premium_rate *= 1.15
                    elif risk_level == "Moderate to High":
                        base_premium_rate *= 1.30
                    elif risk_level == "High":
                        base_premium_rate *= 1.50

                    st.info(f"""
                    **Latest 2024 Data:**
                    - Sum Insured: {suminsured}
                    - Net Premium: {netpremium}
                    - Risk Level: {risk_level}
                    """)

                    st.success(f"💰 Estimated 2025 Premium Rate: {base_premium_rate:.2f}%")

                    update_vehicle_risk_premium(st.session_state['risk_id'], base_premium_rate)
                    st.success("✅ Premium saved to vehicle_risk.")

                else:
                    st.error("❌ No data found for 2024 for this make/submake!")

            else:
                row = get_latest_suminsured_netpremium(make_name, sub_make_name, model_year)
                if row and row[0] and row[1]:
                    suminsured, netpremium = row

                    tracker_id = get_tracker_id(make_name, sub_make_name, model_year)
                    risk_level = get_risk_level(st.session_state['risk_id'])

                    premium_rate = (netpremium / suminsured) * 100

                    if risk_level == "Low":
                        premium_rate *= 1.10
                    elif risk_level == "Low to Moderate":
                        premium_rate *= 1.15
                    elif risk_level == "Moderate to High":
                        premium_rate *= 1.30
                    elif risk_level == "High":
                        premium_rate *= 1.50

                    if tracker_id and tracker_id > 0:
                        premium_rate *= 1.05
                    else:
                        premium_rate *= 1.10

                    st.info(f"""
                    **Fetched Data:**
                    - Sum Insured: {suminsured}
                    - Net Premium: {netpremium}
                    - Tracker ID: {tracker_id}
                    - Risk Level: {risk_level}
                    """)

                    st.success(f"💰 Final Premium Rate: {premium_rate:.2f}%")

                    update_vehicle_risk_premium(st.session_state['risk_id'], premium_rate)
                    st.success("✅ Premium saved to vehicle_risk.")
                else:
                    st.error("❌ No inspection data found for this year!")

elif st.session_state.page == "QA":
    qa.show()

elif st.session_state.page == "Logout":
    st.warning("You have been logged out.")

# ---- FOOTER ----
footer_html = Path("templates/footer.html").read_text(encoding="utf-8")
st.markdown(footer_html, unsafe_allow_html=True)
