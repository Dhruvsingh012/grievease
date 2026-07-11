"""
NLP Model Training Script
Train classification model on grievance dataset using scikit-learn
"""
import os
import pandas as pd
import numpy as np
import re
import string
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
except ImportError:
    print("Please install NLTK: pip install nltk")
    exit(1)

# Download required NLTK data
def download_nltk_data():
    """Download required NLTK resources"""
    resources = ['stopwords', 'wordnet', 'punkt', 'averaged_perceptron_tagger']
    for resource in resources:
        try:
            nltk.data.find(f'corpora/{resource}')
        except LookupError:
            print(f"Downloading {resource}...")
            nltk.download(resource, quiet=True)

download_nltk_data()

# Initialize NLP tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def preprocess_text(text):
    """
    Comprehensive text preprocessing pipeline
    
    Args:
        text: Raw text string
    
    Returns:
        Cleaned and preprocessed text
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove digits
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Tokenization, stopword removal, and lemmatization
    words = text.split()
    words = [
        lemmatizer.lemmatize(word) 
        for word in words 
        if word not in stop_words and len(word) > 2
    ]
    
    return ' '.join(words)


def load_dataset(filepath):
    """
    Load and prepare dataset
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        DataFrame with loaded data
    """
    print(f"Loading dataset from {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"Error: Dataset file not found at {filepath}")
        print("Please run generate_dataset.py first to create the dataset")
        return None
    
    df = pd.read_csv(filepath)
    
    print(f"Dataset loaded: {len(df)} complaints")
    print(f"Categories: {df['category'].nunique()}")
    print(f"\nCategory distribution:")
    print(df['category'].value_counts())
    
    return df


def prepare_data(df):
    """
    Prepare data for training
    
    Args:
        df: Input DataFrame
    
    Returns:
        Tuple of (X, y) where X is text data and y is labels
    """
    print("\nPreprocessing text data...")
    
    # Apply preprocessing
    df['processed_text'] = df['description'].apply(preprocess_text)
    
    # Remove empty processed texts
    df = df[df['processed_text'].str.len() > 0]
    
    X = df['processed_text']
    y = df['category']
    
    print(f"Data prepared: {len(X)} samples")
    
    return X, y


def train_model(X_train, y_train, X_test, y_test, model_type='logistic'):
    """
    Train classification model
    
    Args:
        X_train: Training features (text)
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        model_type: 'logistic' or 'naive_bayes'
    
    Returns:
        Tuple of (model, vectorizer, accuracy)
    """
    print(f"\nTraining {model_type} model...")
    
    # TF-IDF Vectorization
    print("Creating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2),
        sublinear_tf=True
    )
    
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    print(f"Feature matrix shape: {X_train_tfidf.shape}")
    
    # Train model
    if model_type == 'logistic':
        model = LogisticRegression(
            max_iter=1000,
            C=1.0,
            solver='lbfgs',
            multi_class='multinomial',
            random_state=42
        )
    else:  # naive_bayes
        model = MultinomialNB(alpha=0.1)
    
    print("Training model...")
    model.fit(X_train_tfidf, y_train)
    
    # Predictions
    print("Making predictions...")
    y_pred = model.predict(X_test_tfidf)
    
    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n{'='*60}")
    print(f"Model: {model_type.upper()}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"{'='*60}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return model, vectorizer, accuracy, y_pred


def plot_confusion_matrix(y_test, y_pred, categories):
    """
    Plot confusion matrix
    
    Args:
        y_test: True labels
        y_pred: Predicted labels
        categories: List of category names
    """
    cm = confusion_matrix(y_test, y_pred, labels=categories)
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=categories,
        yticklabels=categories
    )
    plt.title('Confusion Matrix - Complaint Category Prediction')
    plt.ylabel('Actual Category')
    plt.xlabel('Predicted Category')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(os.path.dirname(__file__), 'confusion_matrix.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"\nConfusion matrix saved to {plot_path}")
    plt.close()


def save_model(model, vectorizer, model_path, vectorizer_path):
    """
    Save trained model and vectorizer
    
    Args:
        model: Trained model
        vectorizer: Fitted vectorizer
        model_path: Path to save model
        vectorizer_path: Path to save vectorizer
    """
    print(f"\nSaving model to {model_path}...")
    joblib.dump(model, model_path)
    
    print(f"Saving vectorizer to {vectorizer_path}...")
    joblib.dump(vectorizer, vectorizer_path)
    
    print("Model and vectorizer saved successfully!")


def main():
    """Main training pipeline"""
    print("="*60)
    print("GrievEase NLP Model Training Pipeline")
    print("="*60)
    
    # Paths - Using multiple fallback methods
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try Method 1: Relative to script location (app/ml/train_model.py)
    backend_dir = os.path.dirname(os.path.dirname(current_dir))
    dataset_path = os.path.join(backend_dir, 'dataset', 'complaints.csv')
    
    # Try Method 2: If running from backend directory
    if not os.path.exists(dataset_path):
        dataset_path = os.path.join(os.getcwd(), 'dataset', 'complaints.csv')
    
    # Try Method 3: Check parent directories
    if not os.path.exists(dataset_path):
        cwd = os.getcwd()
        dataset_path = os.path.join(cwd, 'backend', 'dataset', 'complaints.csv')
    
    model_path = os.path.join(current_dir, 'model.pkl')
    vectorizer_path = os.path.join(current_dir, 'vectorizer.pkl')
    
    print(f"\nCurrent working directory: {os.getcwd()}")
    print(f"Script location: {current_dir}")
    print(f"Looking for dataset at: {dataset_path}")
    print(f"Dataset exists: {os.path.exists(dataset_path)}\n")
    
    # Load dataset
    df = load_dataset(dataset_path)
    if df is None:
        return
    
    # Prepare data
    X, y = prepare_data(df)
    
    # Split data
    print("\nSplitting data into train/test sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Logistic Regression
    model_lr, vectorizer_lr, acc_lr, y_pred_lr = train_model(
        X_train, y_train, X_test, y_test,
        model_type='logistic'
    )
    
    # Train Naive Bayes
    model_nb, vectorizer_nb, acc_nb, y_pred_nb = train_model(
        X_train, y_train, X_test, y_test,
        model_type='naive_bayes'
    )
    
    # Select best model
    if acc_lr >= acc_nb:
        print(f"\n{'='*60}")
        print("Selected Model: Logistic Regression")
        print(f"Final Accuracy: {acc_lr:.4f} ({acc_lr*100:.2f}%)")
        print(f"{'='*60}")
        best_model = model_lr
        best_vectorizer = vectorizer_lr
        best_pred = y_pred_lr
    else:
        print(f"\n{'='*60}")
        print("Selected Model: Naive Bayes")
        print(f"Final Accuracy: {acc_nb:.4f} ({acc_nb*100:.2f}%)")
        print(f"{'='*60}")
        best_model = model_nb
        best_vectorizer = vectorizer_nb
        best_pred = y_pred_nb
    
    # Plot confusion matrix
    categories = sorted(y.unique())
    plot_confusion_matrix(y_test, best_pred, categories)
    
    # Save model
    save_model(best_model, best_vectorizer, model_path, vectorizer_path)
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. The model will be automatically loaded for predictions")
    print("3. Test the API at http://localhost:8000/docs")


if __name__ == "__main__":
    main()