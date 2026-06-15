import pickle
import string
import re
import warnings
warnings.filterwarnings('ignore')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import numpy as np

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pymorphy3

# Инициализация nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

app = FastAPI(title="Movie Classifier API", description="FastAPI для классификации описаний фильмов")

# Список стоп-слов
russian_stopwords = stopwords.words("russian")
russian_stopwords.extend([
    'т.д.', 'т', 'д', 'это','который','свой','своём','всем','всё','её','оба','ещё','должный',
    "фильм", "кино", "режиссер", "актер", "роль", "герой", "жизнь", "человек",
    "один", "два", "три", "новый", "своем", "всем", "всё", "время", "история"
])

morph = pymorphy3.MorphAnalyzer()

def clean_and_preprocess(text):
    # Очистка
    text = str(text).lower()
    text = ''.join([ch for ch in text if ch not in string.punctuation])
    text = ''.join([i if not i.isdigit() else '' for i in text])
    text = ''.join([i if i.isalpha() else ' ' for i in text])
    text = re.sub(r'\s+', ' ', text, flags=re.I)
    text = re.sub('[a-z]', '', text, flags=re.I)
    st = '❯\xa0—«»'
    text = ''.join([ch if ch not in st else ' ' for ch in text])
    
    # Лемматизация
    tokens = word_tokenize(text)
    res = list()
    for word in tokens:
        p = morph.parse(word)[0]
        res.append(p.normal_form)
    
    # Токенизация и стоп-слова
    final_tokens = [token for token in res if token not in russian_stopwords and len(token) > 2]
    return " ".join(final_tokens)

# Загрузка предобученной модели и векторизатора
try:
    with open('model_rf.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("Модель и векторизатор успешно загружены!")
except Exception as e:
    print(f"Ошибка загрузки модели: {e}")

class TextRequest(BaseModel):
    text: str

@app.post("/predict")
def predict_topic(request: TextRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст запроса пуст")
    
    try:
        clean_txt = clean_and_preprocess(request.text)
        vectorized = vectorizer.transform([clean_txt])
        prediction = model.predict(vectorized)[0]
        probabilities = model.predict_proba(vectorized)[0]
        
        return {
            "predicted_class": int(prediction),
            "probabilities": [float(p) for p in probabilities]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

