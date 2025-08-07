# admin_dashboard.py
import streamlit as st
import json

st.title("Результаты ранжирования кандидатов")

try:
    with open("ranked_candidates.json", "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            st.subheader("Вакансия:")
            st.write(record["job_description"])
            st.subheader("Топ кандидатов:")
            st.write(record["ranked"])
except FileNotFoundError:
    st.info("Пока нет данных о ранжированных кандидатах.")