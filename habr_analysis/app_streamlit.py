import streamlit as st
import requests
import numpy as np
import pandas as pd

st.set_page_config(page_title="Habr Classifier", page_icon="✍", layout="centered")

st.title("✍ Классификатор статей Хабра")
st.write("Введите текст статьи Хабра, и наша модель определит её категорию!")

# Карта тем
topic_names = {
    0: 'Тема 0 – Веб-разработка / Фронтенд',
    1: 'Тема 1 – Data Science / Машинное обучение',
    2: 'Тема 2 – Системное администрирование / DevOps',
    3: 'Тема 3 – Информационная безопасность',
    4: 'Тема 4 – Менеджмент и управление проектами'
}

text_input = st.text_area("Текст статьи Хабра:", height=150, placeholder="Например: Использование Docker для контейнеризации микросервисов...")

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
        st.warning("Пожалуйста, введите текст статьи.")

