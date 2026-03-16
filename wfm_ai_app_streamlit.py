import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Workforce Copilot")

# Upload workforce data
uploaded_file = st.file_uploader("Upload workforce data (CSV)", type="csv")

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("Dataset uploaded successfully")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    question = st.chat_input("Ask a workforce analytics question")

    if question:

        # Show user message
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):

            with st.spinner("Analyzing workforce data..."):

                try:

                    # STEP 1: Generate Pandas query
                    query_prompt = f"""
                    You are a Python data analyst.

                    Dataframe name: df

                    Available columns:
                    {list(df.columns)}

                    Generate ONLY a Pandas query that answers the user's question.

                    Do NOT include markdown.
                    Do NOT include explanation.

                    Question:
                    {question}
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": query_prompt}]
                    )

                    query = response.choices[0].message.content.strip()
                    query = query.replace("```python", "").replace("```", "").strip()

                    # STEP 2: Execute query
                    result = eval(query)

                    if isinstance(result, pd.DataFrame) or isinstance(result, pd.Series):
                        result_text = result.to_string(index=False)
                    else:
                        result_text = str(result)

                    # STEP 3: Ask AI to explain result
                    explain_prompt = f"""
                    You are a workforce analytics assistant.

                    The following result was produced from workforce data:

                    {result_text}

                    User question:
                    {question}

                    Provide the answer in this format:

                    Answer:
                    <short answer>

                    Explanation:
                    <explain why based on the data>

                    Details:
                    <mention employees, hours, or numbers from the result>
                    """

                    explanation = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": explain_prompt}]
                    )

                    answer = explanation.choices[0].message.content

                    st.write(answer)

                    # Save assistant message
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as e:
                    st.error(f"Error: {e}")
