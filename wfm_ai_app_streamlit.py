import os
import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Workforce Copilot", layout="wide")
st.title("AI Workforce Copilot")

# -----------------------------
# Workforce Simulator
# -----------------------------
def simulate_workforce(n=500):

    first = ["John","Maria","David","Lisa","Mark","Sophia","Daniel","Emma","Michael","Olivia"]
    last = ["Smith","Johnson","Brown","Lee","Garcia","Martinez","Taylor","Anderson","Thomas","Wilson"]

    departments = ["Sales","Support","Operations","IT","HR","Finance"]
    shifts = ["Morning","Evening","Night"]

    rows=[]

    for i in range(1,n+1):

        scheduled = random.randint(35,45)
        actual = scheduled + random.randint(-5,10)

        rows.append({
            "EmployeeID":i,
            "EmployeeName":f"{random.choice(first)} {random.choice(last)}",
            "Department":random.choice(departments),
            "Shift":random.choice(shifts),
            "ScheduledHours":scheduled,
            "ActualHours":actual,
            "Overtime":max(0,actual-40),
            "AbsentDays":random.randint(0,2)
        })

    df=pd.DataFrame(rows)
    return df


# -----------------------------
# Data Source
# -----------------------------
st.sidebar.header("Data Source")

use_csv = st.sidebar.checkbox("Upload CSV")

if use_csv:

    file = st.sidebar.file_uploader("Upload CSV", type="csv")

    if file:
        df = pd.read_csv(file)
    else:
        st.warning("Upload CSV")
        st.stop()

else:
    df = simulate_workforce()

st.subheader("Dataset Sample")
st.dataframe(df.sample(10))


# -----------------------------
# Chat Memory
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages=[]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# -----------------------------
# Chat Input
# -----------------------------
question = st.chat_input("Ask workforce question")

if question:

    st.session_state.messages.append({"role":"user","content":question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Analyzing workforce data..."):

            try:

                # -------------------------
                # Step 1 Generate Query
                # -------------------------
                prompt=f"""

You are a Python data analyst.

The dataframe name is df.

Columns:
{list(df.columns)}

Generate a Pandas query to answer the question.

Return ONLY python code.

Question:
{question}

"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )

                query=response.choices[0].message.content
                query=query.replace("```python","").replace("```","").strip()

                result = eval(query)

                # -------------------------
                # Step 2 Detect if chart needed
                # -------------------------
                chart_prompt=f"""

User asked:
{question}

Query result:
{str(result)[:1000]}

Should this result be visualized as a chart?

Answer only one word:

YES
or
NO

"""

                decision=client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":chart_prompt}]
                )

                show_chart = "YES" in decision.choices[0].message.content.upper()

                # -------------------------
                # Step 3 Display result
                # -------------------------
                if isinstance(result,(pd.DataFrame,pd.Series)):

                    st.dataframe(result)

                    if show_chart and isinstance(result,pd.DataFrame):

                        fig,ax=plt.subplots()

                        result.plot(kind="bar",ax=ax)

                        st.pyplot(fig)

                else:
                    st.write(result)

                # -------------------------
                # Step 4 Explanation
                # -------------------------
                explain_prompt=f"""

User question:
{question}

Result:
{str(result)}

Explain the result in simple workforce analytics language.

"""

                explanation=client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":explain_prompt}]
                )

                answer=explanation.choices[0].message.content

                st.write(answer)

                st.session_state.messages.append({
                    "role":"assistant",
                    "content":answer
                })

            except Exception as e:
                st.error(e)
