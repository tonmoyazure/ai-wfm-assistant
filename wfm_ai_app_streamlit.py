import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Workforce Copilot")

# Load workforce data
df = pd.read_csv("workforce_data.csv")

st.subheader("Workforce Data")
st.dataframe(df)

# User question
question = st.text_input("Ask a workforce question")

if st.button("Ask AI") and question:

    st.write("Generating query using AI...")

    try:

        # Step 1: Ask LLM to generate Pandas query
        query_prompt = f"""
        You are a Python data analyst.

        The dataframe name is df.

        Columns available:
        {list(df.columns)}

        Generate ONLY a Pandas query to answer the question.

        Example:
        Question: Who worked more than 40 hours?
        Query: df[df["Hours"] > 40]

        Question:
        {question}

        Return ONLY the Pandas query.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query_prompt}]
        )

        query = response.choices[0].message.content.strip()

        st.subheader("Generated Pandas Query")
        st.code(query)

        # Step 2: Execute query
        result = eval(query)

        st.subheader("Query Result")
        st.write(result)

        # Step 3: Ask AI to explain result
        explanation_prompt = f"""
        Explain this workforce analytics result in simple terms:

        {result}
        """

        explanation = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": explanation_prompt}]
        )

        st.subheader("AI Explanation")
        st.write(explanation.choices[0].message.content)

    except Exception as e:
        st.error(f"Error: {e}")
