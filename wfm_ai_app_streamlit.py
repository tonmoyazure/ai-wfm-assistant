import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# Read API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Workforce Assistant")

df = pd.read_csv("workforce_data.csv")

st.dataframe(df)

question = st.text_input("Ask a workforce question")

if st.button("Ask AI"):
    data_text = df.to_string(index=False)

    prompt = f"""
    You are a workforce analytics assistant.

    Workforce data:
    {data_text}

    Answer the question:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    st.write(response.choices[0].message.content)
