import streamlit as st
import requests
import numpy as np
import pandas as pd

st.set_page_config(page_title="Movie Classifier", page_icon="🎬", layout="centered")

st.title("🎬 Классификатор фильмов")
st.write("Введите описание фильма, и наша модель определит его тему!")

# Карта тем
topic_names = {
    0: '0 - Герой и судьба человека',
    1: '1 – Детективы и расследования',
    2: '2 – Военная драма / История',
    3: '3 – Научная фантастика / Время',
    4: '4 – Семейные отношения / Драма',
    5: '5 – Любовь и романтика',
    6: '6 – Приключения / Пираты'
}

text_input = st.text_area("Описание фильма:", height=150, placeholder="Например: Группа исследователей отправляется в путешествие во времени...")

if st.button("Определить категорию"):
    if text_input.strip():
        with st.spinner("Классификация текста..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/predict", 
                    json={"text": text_input}
                )
                if response.status_code == 200:
                    result = response.json()
                    pred_class = result["predicted_class"]
                    probs = result["probabilities"]
                    
                    st.success(f"**Предсказанный класс:** {topic_names.get(pred_class, f'Тема {pred_class}')}")
                    
                    # Построение графика вероятностей
                    prob_df = pd.DataFrame({
                        'Тема': [topic_names.get(i, f'Тема {i}') for i in range(len(probs))],
                        'Вероятность': probs
                    })
                    st.write("### Распределение вероятностей:")
                    st.bar_chart(prob_df.set_index('Тема'))
                else:
                    st.error(f"Ошибка сервера: {response.json().get('detail', 'Неизвестная ошибка')}")
            except Exception as e:
                st.error(f"Не удалось подключиться к FastAPI бэкенду. Убедитесь, что он запущен на http://127.0.0.1:8000. Ошибка: {e}")
    else:
        st.warning("Пожалуйста, введите текст описания.")

