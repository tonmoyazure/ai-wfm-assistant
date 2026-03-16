import os
import streamlit as st
import pandas as pd
import random
from openai import OpenAI

# ------------------------------
# Initialize OpenAI client
# ------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Workforce Copilot", layout="wide")
st.title("AI Workforce Copilot - Chat Interface with CSV / Simulator")

# ------------------------------
# Workforce Simulator
# ------------------------------
def simulate_workforce(n_employees=500):
    first_names = ["John", "Maria", "David", "Lisa", "Mark", "Sophia", "Daniel", "Emma", "Michael", "Olivia"]
    last_names = ["Smith", "Johnson", "Brown", "Lee", "Garcia", "Martinez", "Taylor", "Anderson", "Thomas", "Wilson"]
    departments = ["Sales", "Support", "Operations", "IT", "HR", "Finance"]
    shifts = ["Morning", "Evening", "Night"]

    data = []
    for i in range(1, n_employees + 1):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept = random.choice(departments)
        scheduled_hours = random.randint(35, 45)
        actual_hours = scheduled_hours + random.randint(-5, 10)
        overtime = max(0, actual_hours - 40)
        absent_days = random.randint(0, 2)
        shift = random.choice(shifts)

        data.append({
            "EmployeeID": i,
            "EmployeeName": name,
            "Department": dept,
            "ScheduledHours": scheduled_hours,
            "ActualHours": actual_hours,
            "Overtime": overtime,
            "AbsentDays": absent_days,
            "Shift": shift
        })

    df = pd.DataFrame(data)

    # Staffing shortages per department
    dept_summary = df.groupby("Department").apply(lambda x: sum(x["ScheduledHours"] - x["ActualHours"])).reset_index()
    dept_summary.columns = ["Department", "StaffingShortage"]
    df = df.merge(dept_summary, on="Department", how="left")
    return df

# ------------------------------
# Load Data
# ------------------------------
st.sidebar.header("Data Options")
use_csv = st.sidebar.checkbox("Upload CSV file instead of simulator", value=False)

if use_csv:
    uploaded_file = st.sidebar.file_uploader("Upload workforce CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Workforce Data (sample 10 rows)")
        st.dataframe(df.sample(10))
    else:
        st.warning("Upload a CSV file or disable CSV option to use simulator.")
        st.stop()
else:
    df = simulate_workforce(n_employees=500)
    st.subheader("Simulated Workforce Data (sample 10 rows)")
    st.dataframe(df.sample(10))

# ------------------------------
# Initialize session chat memory
# ------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat conversation
chat_placeholder = st.container()
with chat_placeholder:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div style='text-align:right; background-color:#DCF8C6; padding:8px; border-radius:8px; margin:4px;'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left; background-color:#F1F0F0; padding:8px; border-radius:8px; margin:4px;'>{message['content']}</div>", unsafe_allow_html=True)

# ------------------------------
# Chat input
# ------------------------------
question = st.text_input("Ask a workforce question here...")

if st.button("Send") and question:
    st.session_state.messages.append({"role": "user", "content": question})
    st.experimental_rerun()  # refresh to show user message

# ------------------------------
# AI response
# ------------------------------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    question = st.session_state.messages[-1]["content"]

    with st.spinner("AI is analyzing workforce data..."):
        try:
            # Step 1: Generate Pandas query using conversation memory
            query_prompt = f"""
            You are a Python data analyst assistant.
            The dataframe is named df with columns: {list(df.columns)}.
            Previous conversation: {st.session_state.messages}
            Generate ONLY a Pandas query to answer the user's latest question.
            Do not include markdown, explanation, or comments.
            Latest user question: {question}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": query_prompt}]
            )

            query = response.choices[0].message.content.strip()
            query = query.replace("```python", "").replace("```", "").strip()

            # Step 2: Execute query
            result = eval(query)

            if isinstance(result, pd.DataFrame) or isinstance(result, pd.Series):
                result_text = result.to_string(index=False)
            else:
                result_text = str(result)

            # Step 3: Ask AI to explain result
            explain_prompt = f"""
            You are a workforce analytics assistant.
            Previous conversation: {st.session_state.messages}
            Latest result from dataframe: {result_text}
            User question: {question}
            Provide:
            1. Short answer
            2. Explanation based on the dataset
            3. Key employees, departments, or values involved
            """

            explanation = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": explain_prompt}]
            )

            answer = explanation.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})

            st.experimental_rerun()

        except Exception as e:
            st.error(f"Error: {e}")
