import os
import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from openai import OpenAI

# -----------------------------
# OpenAI Setup
# -----------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Workforce Copilot", layout="wide")
st.title("AI Workforce Copilot")

# -----------------------------
# Workforce Simulator
# -----------------------------
def simulate_workforce(n=500):

    first_names = ["John","Maria","David","Lisa","Mark","Sophia","Daniel","Emma","Michael","Olivia"]
    last_names = ["Smith","Johnson","Brown","Lee","Garcia","Martinez","Taylor","Anderson","Thomas","Wilson"]

    departments = ["Sales","Support","Operations","IT","HR","Finance"]
    shifts = ["Morning","Evening","Night"]

    rows = []

    for i in range(1,n+1):

        scheduled = random.randint(35,45)
        actual = scheduled + random.randint(-5,10)

        rows.append({
            "EmployeeID":i,
            "EmployeeName":f"{random.choice(first_names)} {random.choice(last_names)}",
            "Department":random.choice(departments),
            "Shift":random.choice(shifts),
            "ScheduledHours":scheduled,
            "ActualHours":actual,
            "Overtime":max(0,actual-40),
            "AbsentDays":random.randint(0,2)
        })

    return pd.DataFrame(rows)

# -----------------------------
# AI Insight Engine
# -----------------------------
def generate_ai_insights(df):

    insights = []

    # overtime count
    overtime_count = len(df[df["Overtime"] > 0])
    insights.append(f"⚠ {overtime_count} employees are already in overtime.")

    # near overtime
    near_ot = len(df[(df["ActualHours"] >= 38) & (df["ActualHours"] <= 40)])
    insights.append(f"⚠ {near_ot} employees are close to overtime threshold (38–40 hours).")

    # department overtime
    dept_ot = df.groupby("Department")["Overtime"].sum().sort_values(ascending=False)

    if len(dept_ot) > 0:
        insights.append(f"⚠ {dept_ot.index[0]} department has the highest overtime workload.")

    # shift absenteeism
    shift_abs = df.groupby("Shift")["AbsentDays"].sum().sort_values(ascending=False)

    if len(shift_abs) > 0:
        insights.append(f"⚠ {shift_abs.index[0]} shift has the highest absenteeism.")

    return insights


# -----------------------------
# Data Source
# -----------------------------
st.sidebar.header("Data Source")

use_csv = st.sidebar.checkbox("Upload CSV instead of simulator")

if use_csv:

    uploaded_file = st.sidebar.file_uploader("Upload workforce CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        st.subheader("Uploaded Dataset Sample")

        sample_size = min(len(df),10)
        st.dataframe(df.sample(sample_size))

    else:
        st.warning("Please upload a CSV file")
        st.stop()

else:

    df = simulate_workforce()

    st.subheader("Simulated Dataset Sample")

    sample_size = min(len(df),10)
    st.dataframe(df.sample(sample_size))


# -----------------------------
# AI Workforce Insights
# -----------------------------
st.subheader("AI Workforce Insights")

insights = generate_ai_insights(df)

for insight in insights:
    st.warning(insight)


# -----------------------------
# Chat Memory
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# -----------------------------
# Chat Input
# -----------------------------
question = st.chat_input("Ask a workforce analytics question")

if question:

    st.session_state.messages.append({
        "role":"user",
        "content":question
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Analyzing workforce data..."):

            try:

                # -----------------------------
                # Generate Pandas Query
                # -----------------------------
                prompt = f"""

You are a Python data analyst.

The dataframe name is df.

Columns:
{list(df.columns)}

Return ONLY a valid Pandas query.

Rules:
- Return ONE line of Python
- No explanation
- No markdown
- No text

Examples:

df["Overtime"].sum()

df.groupby("Department")["Overtime"].sum()

df[df["ActualHours"] > 45]

User question:
{question}

"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )

                query = response.choices[0].message.content.strip()

                # Clean query
                query = query.replace("```python","").replace("```","")

                lines = query.split("\n")

                clean_lines = []

                for line in lines:
                    if "df" in line:
                        clean_lines.append(line.strip())

                if clean_lines:
                    query = clean_lines[0]
                else:
                    query = lines[-1].strip()

                # -----------------------------
                # Execute Query Safely
                # -----------------------------
                try:
                    result = eval(query)
                except:
                    st.warning("AI generated an invalid query. Please rephrase.")
                    st.stop()

                # -----------------------------
                # Display Results
                # -----------------------------
                if isinstance(result,(pd.DataFrame,pd.Series)):

                    st.dataframe(result)

                    if isinstance(result,pd.DataFrame) and len(result.columns) >= 2:

                        try:
                            fig, ax = plt.subplots()
                            result.plot(kind="bar", ax=ax)
                            st.pyplot(fig)
                        except:
                            pass

                    result_text = result.to_string()

                else:

                    st.write(result)
                    result_text = str(result)

                # -----------------------------
                # AI Explanation
                # -----------------------------
                explain_prompt = f"""

You are a workforce analytics assistant.

User Question:
{question}

Result from dataset:
{result_text}

Provide:
1. Short answer
2. Explanation
3. Key workforce insights

"""

                explanation = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":explain_prompt}]
                )

                answer = explanation.choices[0].message.content

                st.write(answer)

                st.session_state.messages.append({
                    "role":"assistant",
                    "content":answer
                })

            except Exception as e:

                st.error(f"Error: {e}")
