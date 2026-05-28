import sys
import os
import re
import pickle
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import pymorphy3


sys.stdout.reconfigure(encoding='utf-8')


try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except Exception as e:
    print(f"Warning: NLTK download failed: {e}")

app = FastAPI(title="Language Identification API", version="6.7")

MODEL_PATH = "best_model.pkl"
DATASET_PATH = "TextLanguage.csv"

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file '{MODEL_PATH}' not found. Please run the training pipeline first.")

with open(MODEL_PATH, "rb") as f:
    pipeline = pickle.load(f)


nltk_lang_map = {
    'English': 'english', 'Russian': 'russian', 'Spanish': 'spanish',
    'Portugeese': 'portuguese', 'Italian': 'italian', 'French': 'french',
    'Dutch': 'dutch', 'German': 'german', 'Danish': 'danish',
    'Sweedish': 'swedish', 'Arabic': 'arabic', 'Turkish': 'turkish',
    'Greek': 'greek'
}

custom_stopwords = {
    'English': {'wikipedia', 'article', 'articles', 'page', 'pages', 'one', 'two', 'many', 'also', 'would', 'like', 'get', 'use', 'used', 'using', 'first', 'new', 'well', 'may'},
    'Russian': {'это', 'также', 'например', 'года', 'году', 'могут', 'является', 'быть', 'время', 'однако', 'очень', 'просто', 'могу', 'сказать', 'можете', 'своей', 'который', 'которые', 'которая', 'которого', 'наш', 'хочу', 'даже', 'слово', 'слова'},
    'Spanish': {'wikipedia', 'artículo', 'artículos', 'si', 'bien', 'puede', 'ser', 'solo', 'así', 'cada', 'dos', 'hacer', 'tener', 'como', 'más', 'pero', 'todo', 'también'},
    'German': {'wikipedia', 'artikel', 'hast', 'kannst', 'gut', 'wäre', 'oh', 'tut', 'sagen', 'sehen', 'wirklich', 'jemand', 'mehr', 'immer', 'schon', 'mal', 'gibt'},
    'Arabic': {'يكيبيديا', 'ويكيبيديا', 'صفحة', 'صفحات', 'أنه', 'يمكن', 'خلال', 'تلك', 'حيث', 'عندما', 'أيضا', 'حتى', 'تم', 'كانت', 'يكون'}
}

stop_words_dict = {}
for lang, nltk_name in nltk_lang_map.items():
    try:
        stops = set(stopwords.words(nltk_name))
    except:
        stops = set()
    if lang in custom_stopwords:
        stops.update(custom_stopwords[lang])
    stop_words_dict[lang] = stops

morph = pymorphy3.MorphAnalyzer()
pymorphy_cache = {}

def lemmatize_russian(word):
    if word not in pymorphy_cache:
        pymorphy_cache[word] = morph.parse(word)[0].normal_form
    return pymorphy_cache[word]

stemmers = {}
for lang_name, nltk_name in [
    ('English', 'english'),
    ('Spanish', 'spanish'),
    ('Portugeese', 'portuguese'),
    ('Italian', 'italian'),
    ('French', 'french'),
    ('Dutch', 'dutch'),
    ('German', 'german'),
    ('Danish', 'danish'),
    ('Sweedish', 'swedish'),
    ('Arabic', 'arabic')
]:
    try:
        stemmers[lang_name] = SnowballStemmer(nltk_name)
    except Exception as e:
        print(f"Warning: could not initialize stemmer for {lang_name}: {e}")

def preprocess_text(text: str, language: str, stem: bool = True) -> str:
    text = str(text).lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    
    if language == 'Russian':
        text = re.sub(r'[^а-яё\s]', ' ', text)
    elif language == 'Arabic':
        text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    elif language == 'Greek':
        text = re.sub(r'[^\u0370-\u03FF\s]', ' ', text)
    elif language == 'Hindi':
        text = re.sub(r'[^\u0900-\u097F\s]', ' ', text)
    elif language == 'Tamil':
        text = re.sub(r'[^\u0B80-\u0BFF\s]', ' ', text)
    elif language == 'Kannada':
        text = re.sub(r'[^\u0C80-\u0CFF\s]', ' ', text)
    elif language == 'Malayalam':
        text = re.sub(r'[^\u0D00-\u0D7F\s]', ' ', text)
    else:
        text = re.sub(r'[^a-zà-ÿœæ\s]', ' ', text)
        
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    
    lang_stops = stop_words_dict.get(language, set())
    words = [w for w in words if w not in lang_stops]
    
    if stem:
        if language == 'Russian':
            words = [lemmatize_russian(w) for w in words]
        elif language in stemmers:
            words = [stemmers[language].stem(w) for w in words]
    else:
        if language == 'Russian':
            words = [lemmatize_russian(w) for w in words]
            
    return ' '.join(words)


print("Calculating dataset stats on startup...")
try:
    df_raw = pd.read_csv(DATASET_PATH)
    total_records = len(df_raw)
    lang_counts = df_raw['Language'].value_counts().to_dict()
    df_raw['char_len'] = df_raw['Text'].astype(str).apply(len)
    avg_length = float(df_raw['char_len'].mean())
    min_length = int(df_raw['char_len'].min())
    max_length = int(df_raw['char_len'].max())
    
    dataset_stats = {
        "total_records": total_records,
        "unique_languages_count": len(lang_counts),
        "avg_text_length": round(avg_length, 2),
        "min_text_length": min_length,
        "max_text_length": max_length,
        "language_distribution": lang_counts
    }
except Exception as e:
    print(f"Error loading stats: {e}")
    dataset_stats = {"error": "Failed to load stats."}


class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    language: str
    confidence: float
    probabilities: Dict[str, float]

@app.post("/api/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    

    text_sample = request.text
    cyrillic_chars = len(re.findall(r'[а-яА-ЯёЁ]', text_sample))
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text_sample))
    greek_chars = len(re.findall(r'[\u0370-\u03FF]', text_sample))
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text_sample))
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text_sample))
    kannada_chars = len(re.findall(r'[\u0C80-\u0CFF]', text_sample))
    malayalam_chars = len(re.findall(r'[\u0D00-\u0D7F]', text_sample))
    

    guessed_lang_group = 'Latin'
    if cyrillic_chars > 2:
        guessed_lang_group = 'Russian'
    elif arabic_chars > 2:
        guessed_lang_group = 'Arabic'
    elif greek_chars > 2:
        guessed_lang_group = 'Greek'
    elif hindi_chars > 2:
        guessed_lang_group = 'Hindi'
    elif tamil_chars > 2:
        guessed_lang_group = 'Tamil'
    elif kannada_chars > 2:
        guessed_lang_group = 'Kannada'
    elif malayalam_chars > 2:
        guessed_lang_group = 'Malayalam'

    cleaned = preprocess_text(request.text, guessed_lang_group)
    

    if not cleaned.strip():
        cleaned = re.sub(r'\s+', ' ', request.text).strip()
        
    try:

        probs = pipeline.predict_proba([cleaned])[0]
        classes = pipeline.classes_
        

        prob_dict = {classes[i]: float(probs[i]) for i in range(len(classes))}

        sorted_probs = dict(sorted(prob_dict.items(), key=lambda item: item[1], reverse=True))
        

        best_lang = max(prob_dict, key=prob_dict.get)
        best_conf = prob_dict[best_lang]
        
        return PredictResponse(
            language=best_lang,
            confidence=round(best_conf, 4),
            probabilities={k: round(v, 4) for k, v in sorted_probs.items()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction error: {str(e)}")

@app.get("/api/stats")
def get_stats():
    return dataset_stats


@app.get("/")
def read_index():
    index_path = os.path.join("app", "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)


app.mount("/app", StaticFiles(directory="app"), name="app")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
