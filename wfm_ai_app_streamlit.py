import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Workforce Copilot")

# Load CSV
df = pd.read_csv("workforce_data.csv")

st.subheader("Workforce Data")
st.dataframe(df)

question = st.text_input("Ask a workforce question")

if st.button("Ask AI") and question:

    try:

        # Step 1: Generate Pandas query
        query_prompt = f"""
        You are a Python data analyst.

        The dataframe name is df.

        Available columns:
        {list(df.columns)}

        Generate ONLY a Pandas query to answer the question.
        Do NOT include markdown or explanation.

        Question:
        {question}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query_prompt}]
        )

        query = response.choices[0].message.content.strip()
        query = query.replace("```python", "").replace("```", "").strip()

        # Step 2: Execute query
        result = eval(query)

        # Convert result to readable text
        if isinstance(result, pd.DataFrame) or isinstance(result, pd.Series):
            result_text = result.to_string(index=False)
        else:
            result_text = str(result)

        # Step 3: Ask AI to explain
        explain_prompt = f"""
        The following workforce data result was produced:

        {result_text}

        Answer the user's question clearly.

        Question:
        {question}
        """

        explanation = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": explain_prompt}]
        )

        st.subheader("AI Answer")
        st.write(explanation.choices[0].message.content)

    except Exception as e:
        st.error(f"Error: {e}")
