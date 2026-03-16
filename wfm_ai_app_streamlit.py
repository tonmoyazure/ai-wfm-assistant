import os
import streamlit as st
import pandas as pd
import random
from openai import OpenAI

# ----------------------------
# OpenAI client
# ----------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Workforce Copilot", layout="wide")
st.title("AI Workforce Copilot")

# ----------------------------
# Workforce Simulator
# ----------------------------
def simulate_workforce(n_employees=500):

    first_names = ["John","Maria","David","Lisa","Mark","Sophia","Daniel","Emma","Michael","Olivia"]
    last_names = ["Smith","Johnson","Brown","Lee","Garcia","Martinez","Taylor","Anderson","Thomas","Wilson"]

    departments = ["Sales","Support","Operations","IT","HR","Finance"]
    shifts = ["Morning","Evening","Night"]

    data = []

    for i in range(1, n_employees+1):

        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept = random.choice(departments)

        scheduled_hours = random.randint(35,45)
        actual_hours = scheduled_hours + random.randint(-5,10)

        overtime = max(0, actual_hours-40)

        absent_days = random.randint(0,2)

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

    # staffing shortage per department
    dept_summary = df.groupby("Department").apply(
        lambda x: sum(x["ScheduledHours"]-x["ActualHours"])
    ).reset_index()

    dept_summary.columns = ["Department","StaffingShortage"]

    df = df.merge(dept_summary, on="Department", how="left")

    return df


# ----------------------------
# Data Source Selection
# ----------------------------
st.sidebar.header("Data Source")

use_csv = st.sidebar.checkbox("Upload CSV instead of simulator")

if use_csv:

    uploaded_file = st.sidebar.file_uploader("Upload workforce CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        st.subheader("Uploaded Workforce Data (Sample)")
        st.dataframe(df.head(10))

    else:
        st.warning("Upload a CSV file")
        st.stop()

else:

    df = simulate_workforce(500)

    st.subheader("Simulated Workforce Data (Sample)")
    st.dataframe(df.sample(10))


# ----------------------------
# Chat Memory
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display previous chat
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# ----------------------------
# Chat Input
# ----------------------------
question = st.chat_input("Ask a workforce analytics question")

if question:

    # Save user message
    st.session_state.messages.append({
        "role":"user",
        "content":question
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Analyzing workforce data..."):

            try:

                # ----------------------------------
                # Step 1: Generate Pandas Query
                # ----------------------------------
                prompt = f"""

You are a Python data analyst.

The dataframe name is df.

Columns:
{list(df.columns)}

Generate ONLY a Pandas query to answer the question.

Do NOT include explanation or markdown.

Question:
{question}

"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )

                query = response.choices[0].message.content.strip()

                query = query.replace("```python","").replace("```","")

                # ----------------------------------
                # Step 2: Execute Query
                # ----------------------------------
                result = eval(query)

                if isinstance(result,(pd.DataFrame,pd.Series)):
                    result_text = result.to_string(index=False)
                else:
                    result_text = str(result)

                # ----------------------------------
                # Step 3: AI Explanation
                # ----------------------------------
                explain_prompt = f"""

You are a workforce analytics assistant.

User question:
{question}

Result from dataset:
{result_text}

Provide:

1) Short answer  
2) Explanation  
3) Key insights

"""

                explanation = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":explain_prompt}]
                )

                answer = explanation.choices[0].message.content

                st.write(answer)

                # Save assistant response
                st.session_state.messages.append({
                    "role":"assistant",
                    "content":answer
                })

            except Exception as e:

                st.error(f"Error: {e}")
