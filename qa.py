import streamlit as st
from datetime import datetime
from utils.db_utils import get_vehicle_claims
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

def show():
    st.subheader("🧾 Do you need motor insurance?")

    llm = Ollama(model="llama3")

    if 'motor_insurance' not in st.session_state:
        st.session_state.motor_insurance = None

    if st.session_state.motor_insurance is None:
        col1, col2 = st.columns(2)
        if col1.button("✅ Yes"):
            st.session_state.motor_insurance = True
        if col2.button("❌ No"):
            st.session_state.motor_insurance = False

    elif st.session_state.motor_insurance is True:
        make_name = st.text_input("Enter Make Name")
        if make_name:
            sub_make_name = st.text_input("Enter Sub Make Name")
            if sub_make_name:
                model_year = st.number_input(
                    "Enter Model Year",
                    min_value=1990,
                    max_value=datetime.now().year
                )
                if model_year:
                    suminsured = st.number_input("Enter Sum Insured")
                    if suminsured:
                        driver_age = st.number_input("Enter Driver Age", min_value=18, max_value=100)
                        if driver_age:
                            if st.button("Calculate Risk & Premium"):
                                with st.spinner("🔄 Please wait... Calculating risk profile & premium..."):
                                # 1️⃣ Average of last 5 years
                                 current_year = datetime.now().year
                                 avg_claims = []
                                 avg_capacity = []

                                for y in range(current_year - 5, current_year):
                                    row = get_vehicle_claims(make_name, sub_make_name, y)
                                    if row and row[0] is not None and row[1] is not None:
                                        avg_claims.append(row[0])
                                        avg_capacity.append(row[1])

                                if avg_claims and avg_capacity:
                                    avg_no_of_claims = sum(avg_claims) / len(avg_claims)
                                    avg_vehicle_capacity = sum(avg_capacity) / len(avg_capacity)

                                    # 2️⃣ Risk logic
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

                                    # 3️⃣ Premium
                                    base_premium = (suminsured / 1_000_000) * 2
                                    if risk_level == "Low":
                                        premium_rate = base_premium * 1.10
                                    elif risk_level == "Low to Moderate":
                                        premium_rate = base_premium * 1.20
                                    elif risk_level == "Moderate to High":
                                        premium_rate = base_premium * 1.35
                                    else:
                                        premium_rate = base_premium * 1.50

                                    # ✅ 4️⃣ ✅ Use LLMChain not load_qa_chain!
                                    template = PromptTemplate(
                                        input_variables=["risk_level", "premium_rate", "claims", "capacity"],
                                        template="""
                                        Explain to the user why their vehicle risk level is {risk_level} 
                                        and why the premium rate is {premium_rate:.2f}% based on 
                                        average claims {claims:.2f} and capacity {capacity:.2f}.
                                        """
                                    )

                                    chain = LLMChain(llm=llm, prompt=template)
                                    response = chain.invoke({
                                        "risk_level": risk_level,
                                        "premium_rate": premium_rate,
                                        "claims": avg_no_of_claims,
                                        "capacity": avg_vehicle_capacity
                                    })

                                    explanation = response['text']

                                    st.success(
                                        f"""
                                        ✅ **Summary:**
                                        - Make: {make_name}
                                        - Sub Make: {sub_make_name}
                                        - Model Year: {model_year}
                                        - Sum Insured: {suminsured}
                                        - Driver Age: {driver_age}

                                        📌 **Risk Level:** {risk_level}  
                                        💰 **Estimated Premium:** {premium_rate:.2f}%

                                        **LLM Explanation:**  
                                        {explanation}
                                        """
                                    )
                                else:
                                    st.error("❌ Not enough data found for the last 5 years!")

    elif st.session_state.motor_insurance is False:
        st.info("If you need any information related to other insurance then give me your details, our representative will contact you shortly.")

        name = st.text_input("Your Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")

        if st.button("Submit"):
            st.success(f"✅ Thank you {name}! Our representative will contact you shortly.")
