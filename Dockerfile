FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8080

CMD streamlit run wfm_ai_app_streamlit.py --server.port=8080 --server.address=0.0.0.0