"""
NLP Module - GrievEase v3.0
TF-IDF + Logistic Regression for complaint category prediction.
Falls back to keyword matching if model not trained yet.
"""
import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MODEL_PATH     = "app/ml/category_model.pkl"
VECTORIZER_PATH= "app/ml/category_vectorizer.pkl"

model      = None
vectorizer = None
MODEL_LOADED = False

# ── Training Data ────────────────────────────────────────────────────────────
TRAINING_DATA = [
    # Academic
    ("marks not updated in portal", "Academic"),
    ("attendance shortage problem", "Academic"),
    ("faculty not teaching properly", "Academic"),
    ("grades wrong in result", "Academic"),
    ("syllabus not completed by teacher", "Academic"),
    ("assignment submission issue", "Academic"),
    ("lecture not happening regularly", "Academic"),
    ("professor behaviour problem", "Academic"),
    ("internal marks discrepancy", "Academic"),
    ("academic calendar not followed", "Academic"),
    ("project guide not available", "Academic"),
    ("practical classes not conducted", "Academic"),
    ("course material not provided", "Academic"),
    ("mentor not available for guidance", "Academic"),

    # Administration
    ("bonafide certificate not issued", "Administration"),
    ("migration certificate pending", "Administration"),
    ("documents not processed by office", "Administration"),
    ("character certificate required", "Administration"),
    ("admin staff rude behaviour", "Administration"),
    ("office not responding to requests", "Administration"),
    ("scholarship form not accepted", "Administration"),
    ("transfer certificate delay", "Administration"),
    ("duplicate marksheet request", "Administration"),
    ("college leaving certificate pending", "Administration"),

    # Examination
    ("result not declared yet", "Examination"),
    ("re-evaluation application pending", "Examination"),
    ("hall ticket not generated", "Examination"),
    ("exam schedule clash", "Examination"),
    ("supplementary exam registration", "Examination"),
    ("grace marks not applied", "Examination"),
    ("wrong paper checked in exam", "Examination"),
    ("answer sheet not returned", "Examination"),
    ("practical exam date conflict", "Examination"),
    ("backlog exam not scheduled", "Examination"),

    # Fees
    ("fee receipt not generated", "Fees"),
    ("excess fee charged this semester", "Fees"),
    ("refund not processed", "Fees"),
    ("scholarship amount not credited", "Fees"),
    ("fee structure changed without notice", "Fees"),
    ("online payment failed but deducted", "Fees"),
    ("hostel fee discrepancy", "Fees"),
    ("fine imposed incorrectly", "Fees"),
    ("tuition fee late fine issue", "Fees"),
    ("fee concession not applied", "Fees"),

    # Hostel
    ("hostel room not allotted", "Hostel"),
    ("mess food quality very bad", "Hostel"),
    ("water supply problem in hostel", "Hostel"),
    ("electricity issue in hostel room", "Hostel"),
    ("hostel bathroom not clean", "Hostel"),
    ("warden not addressing complaints", "Hostel"),
    ("hostel wifi not working", "Hostel"),
    ("room change request pending", "Hostel"),
    ("hostel security issue at night", "Hostel"),
    ("pest infestation in hostel room", "Hostel"),
    ("hostel curfew timing problem", "Hostel"),
    ("roommate conflict resolution needed", "Hostel"),

    # IT Support
    ("unable to login to student portal", "IT Support"),
    ("erp system not working", "IT Support"),
    ("college wifi very slow", "IT Support"),
    ("network not available in campus", "IT Support"),
    ("password reset not working", "IT Support"),
    ("email account not created", "IT Support"),
    ("lab computer not functioning", "IT Support"),
    ("software not installed in computer lab", "IT Support"),
    ("online portal showing error", "IT Support"),
    ("student id card not generated in portal", "IT Support"),
    ("website login issue", "IT Support"),
    ("internet connectivity problem", "IT Support"),

    # Infrastructure
    ("classroom projector broken", "Infrastructure"),
    ("chairs and furniture damaged in room", "Infrastructure"),
    ("leaking roof in classroom", "Infrastructure"),
    ("air conditioning not working", "Infrastructure"),
    ("drinking water cooler not working", "Infrastructure"),
    ("parking space problem on campus", "Infrastructure"),
    ("lift not working in building", "Infrastructure"),
    ("bathroom cleanliness issue in college", "Infrastructure"),
    ("street light broken in campus", "Infrastructure"),
    ("construction noise disrupting class", "Infrastructure"),
    ("building maintenance required", "Infrastructure"),

    # Library
    ("required book not available in library", "Library"),
    ("library fine imposed wrongly", "Library"),
    ("digital library access not working", "Library"),
    ("library timing too short", "Library"),
    ("book not returned properly accounted", "Library"),
    ("journal subscription expired", "Library"),
    ("reading room overcrowded", "Library"),
    ("reference book request pending", "Library"),
    ("library membership not activated", "Library"),

    # Security
    ("laptop stolen from campus", "Security"),
    ("ragging incident reported", "Security"),
    ("outsiders entering campus without check", "Security"),
    ("cctv camera not working near lab", "Security"),
    ("bike theft in parking area", "Security"),
    ("eve teasing complaint campus", "Security"),
    ("gate access card not working", "Security"),
    ("lost item not found in lost and found", "Security"),
    ("security guard misbehaved", "Security"),
    ("suspicious activity on campus", "Security"),

    # Transport
    ("college bus always late", "Transport"),
    ("bus route changed without information", "Transport"),
    ("bus overcrowded daily", "Transport"),
    ("driver rash driving complaint", "Transport"),
    ("bus pass not issued", "Transport"),
    ("bus timing not followed", "Transport"),
    ("bus not available on my route", "Transport"),
    ("bus fee increased without notice", "Transport"),
    ("transport facility very poor", "Transport"),
    ("bus breakdown frequently", "Transport"),
]


# ── Keyword Fallback ─────────────────────────────────────────────────────────
KEYWORDS = {
    "Academic":       ["marks", "grades", "attendance", "faculty", "professor", "teacher", "syllabus",
                       "assignment", "lecture", "result", "study", "class", "academic", "course", "project"],
    "Administration": ["bonafide", "certificate", "documents", "office", "admin", "migration",
                       "character", "scholarship", "transfer", "staff"],
    "Examination":    ["exam", "examination", "result", "re-evaluation", "hall ticket", "supplementary",
                       "revaluation", "backlog", "grace", "paper"],
    "Fees":           ["fee", "fees", "refund", "payment", "receipt", "fine", "dues", "challan",
                       "scholarship amount", "concession"],
    "Hostel":         ["hostel", "mess", "food", "room", "warden", "dormitory", "hostel wifi",
                       "water hostel", "electricity hostel", "roommate"],
    "IT Support":     ["portal", "login", "wifi", "network", "internet", "erp", "website", "password",
                       "computer", "software", "it", "server", "email account"],
    "Infrastructure": ["projector", "classroom", "furniture", "building", "lift", "parking",
                       "construction", "roof", "ac", "air condition", "light", "maintenance"],
    "Library":        ["library", "book", "librarian", "fine library", "journal", "reading room",
                       "digital library", "reference"],
    "Security":       ["stolen", "theft", "ragging", "security", "cctv", "lost", "suspicious",
                       "eve teasing", "gate", "harassment"],
    "Transport":      ["bus", "transport", "route", "driver", "vehicle", "pickup", "drop",
                       "bus pass", "timing bus"],
}


def keyword_predict(text: str) -> str:
    text_lower = text.lower()
    scores = {cat: 0 for cat in KEYWORDS}
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text_lower:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Administration"


# ── Model Training ───────────────────────────────────────────────────────────
def train_model():
    global model, vectorizer, MODEL_LOADED
    os.makedirs("app/ml", exist_ok=True)
    texts  = [t for t, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000, sublinear_tf=True)
    X = vectorizer.fit_transform(texts)

    model = LogisticRegression(max_iter=1000, C=2.0, class_weight="balanced")
    model.fit(X, labels)

    joblib.dump(model,      MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    MODEL_LOADED = True
    print(f"✅ NLP model trained on {len(texts)} samples and saved.")


def load_model():
    global model, vectorizer, MODEL_LOADED
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            model      = joblib.load(MODEL_PATH)
            vectorizer = joblib.load(VECTORIZER_PATH)
            MODEL_LOADED = True
            print("✅ NLP model loaded from disk.")
        except Exception as e:
            print(f"⚠️  Could not load model: {e}. Training fresh model.")
            train_model()
    else:
        print("📚 No saved model found. Training fresh model…")
        train_model()


def predict_category(text: str) -> str:
    if not text or len(text.strip()) < 3:
        return "Administration"
    if MODEL_LOADED and model and vectorizer:
        try:
            X   = vectorizer.transform([text.lower()])
            cat = model.predict(X)[0]
            return cat
        except Exception as e:
            print(f"⚠️  Model predict error: {e}")
    return keyword_predict(text)


# ── Auto-load on import ──────────────────────────────────────────────────────
load_model()
