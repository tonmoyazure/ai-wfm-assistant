import streamlit as st
import pandas as pd

st.title("AI Workforce Assistant - Version 2")

st.title("AI Workforce Assistant")

df = pd.read_csv("workforce_data.csv")

st.subheader("Workforce Data")
st.dataframe(df)

question = st.text_input("Ask a workforce question:")

if question:
    overtime = df[df["HoursWorked"] > 40]
    st.subheader("Employees at Risk of Overtime")
    st.write(overtime)
