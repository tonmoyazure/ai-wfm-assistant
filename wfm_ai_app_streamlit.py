import os
import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from openai import OpenAI

# ----------------------------
# OpenAI Setup
# ----------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Workforce Copilot", layout="wide")
st.title("AI Workforce Copilot")

# ----------------------------
# Workforce Simulator
# ----------------------------
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
            "EmployeeID": i,
            "EmployeeName": f"{random.choice(first_names)} {random.choice(last_names)}",
            "Department": random.choice(departments),
            "Shift": random.choice(shifts),
            "ScheduledHours": scheduled,
            "ActualHours": actual,
            "Overtime": max(0,actual-40),
            "AbsentDays": random.randint(0,2)
        })

    df = pd.DataFrame(rows)

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


# ----------------------------
# Chat Memory
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# ----------------------------
# Chat Input
# ----------------------------
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

                # ----------------------------
                # Step 1: Generate Pandas Query
                # ----------------------------
                prompt = f"""

You are a Python data analyst.

The dataframe name is df.

Columns:
{list(df.columns)}

Generate ONLY a Pandas query that answers the question.

Return ONLY python code.

Question:
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
                query = lines[-1].strip()

                # ----------------------------
                # Step 2: Execute Query Safely
                # ----------------------------
                try:
                    result = eval(query)
                except Exception:
                    st.warning("AI generated an invalid query. Please rephrase your question.")
                    st.stop()

                # ----------------------------
                # Step 3: Display Result
                # ----------------------------
                if isinstance(result,(pd.DataFrame,pd.Series)):

                    st.dataframe(result)

                    # ----------------------------
                    # Chart generation
                    # ----------------------------
                    if isinstance(result,pd.DataFrame) and len(result.columns)>=2:

                        try:
                            fig, ax = plt.subplots()

                            result.plot(kind="bar", ax=ax)

                            st.pyplot(fig)

                        except Exception:
                            pass

                    result_text = result.to_string()

                else:

                    st.write(result)

                    result_text = str(result)

                # ----------------------------
                # Step 4: AI Explanation
                # ----------------------------
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
