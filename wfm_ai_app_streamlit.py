import os
import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.write("API Key Loaded:", os.getenv("OPENAI_API_KEY") is not None)

st.title("AI Workforce Assistant")

df = pd.read_csv("workforce_data.csv")

st.dataframe(df)

question = st.text_input("Ask a workforce question")

if st.button("Ask AI"):

    try:
        data_text = df.to_string(index=False)

        prompt = f"""
        You are a workforce analytics assistant.

        Workforce data:
        {data_text}

        Answer the question:
        {question}
        """

        st.write("Calling OpenAI...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        st.write("Response received from OpenAI")

        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error calling OpenAI: {e}")
