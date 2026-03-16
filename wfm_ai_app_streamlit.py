import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Workforce Copilot")

# Load data
df = pd.read_csv("workforce_data.csv")

st.subheader("Workforce Data")
st.dataframe(df)

question = st.text_input("Ask a workforce question")

if st.button("Ask AI") and question:

    try:

        # Ask AI to generate Pandas query
        prompt = f"""
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
            messages=[{"role": "user", "content": prompt}]
        )

        query = response.choices[0].message.content.strip()

        # Remove markdown if AI adds it
        query = query.replace("```python", "").replace("```", "").strip()

        # Execute query silently
        result = eval(query)

        # Ask AI to explain result
        explain_prompt = f"""
        A workforce analytics query returned this result:

        {result}

        Answer the user's question clearly and concisely.

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
