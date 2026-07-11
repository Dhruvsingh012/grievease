"""
predict.py - GrievEase v3.0
Wrapper kept for backward compatibility.
Main prediction logic is in app/nlp.py
"""
import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH      = os.path.join(BASE_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

model      = None
vectorizer = None


def load_model():
    global model, vectorizer
    if model is None or vectorizer is None:
        try:
            model      = joblib.load(MODEL_PATH)
            vectorizer = joblib.load(VECTORIZER_PATH)
            print("✅ ML model & vectorizer loaded (predict.py)")
        except Exception as e:
            print(f"⚠️  Could not load ML model: {e}")


def predict_category(text: str) -> str:
    load_model()
    if model is None or vectorizer is None:
        return "Administration"
    try:
        return model.predict(vectorizer.transform([text]))[0]
    except Exception:
        return "Administration"
