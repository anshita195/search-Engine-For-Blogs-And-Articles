import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import re

logger = logging.getLogger(__name__)

class TFIDFClassifier:
    """Stage 1 Classifier: Fast TF-IDF + Logistic Regression"""
    
    def __init__(self, model_path: str = "models/tfidf_classifier.pkl"):
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.pipeline = None
        self.is_trained = False
        self._load_model()
    
    def _load_model(self) -> bool:
        try:
            if self.model_path.exists():
                self.pipeline = joblib.load(self.model_path)
                self.is_trained = True
                logger.info(f"Loaded TF-IDF classifier from {self.model_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")
        return False
    
    def _save_model(self) -> None:
        try:
            joblib.dump(self.pipeline, self.model_path)
            logger.info(f"Saved TF-IDF classifier to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def train(self, training_data: List[Dict]) -> bool:
        try:
            logger.info("Training TF-IDF classifier...")
            
            texts = []
            labels = []
            
            for item in training_data:
                text = item.get('text', '')
                is_personal = item.get('is_personal', False)
                
                if text:
                    processed_text = self._preprocess_text(text)
                    if processed_text:
                        texts.append(processed_text)
                        labels.append(1 if is_personal else 0)
            
            if len(texts) < 10:
                logger.error("Insufficient training data")
                return False
            
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=3000,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    stop_words='english'
                )),
                ('classifier', LogisticRegression(random_state=42, max_iter=1000))
            ])
            
            self.pipeline.fit(texts, labels)
            self.is_trained = True
            self._save_model()
            
            logger.info(f"Trained on {len(texts)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training: {e}")
            return False
    
    def predict(self, text: str) -> Tuple[bool, float]:
        if not self.is_trained:
            return False, 0.0
        
        try:
            processed_text = self._preprocess_text(text)
            if not processed_text:
                return False, 0.0
            
            proba = self.pipeline.predict_proba([processed_text])[0]
            is_personal = self.pipeline.predict([processed_text])[0] == 1
            confidence = max(proba)
            
            return bool(is_personal), float(confidence)
            
        except Exception as e:
            logger.error(f"Error predicting: {e}")
            return False, 0.0
    
    def predict_batch(self, texts: List[str]) -> List[Tuple[bool, float]]:
        if not self.is_trained:
            return [(False, 0.0)] * len(texts)
        
        try:
            processed_texts = [self._preprocess_text(text) for text in texts]
            valid_texts = [text for text in processed_texts if text]
            
            if not valid_texts:
                return [(False, 0.0)] * len(texts)
            
            predictions = self.pipeline.predict(valid_texts)
            probas = self.pipeline.predict_proba(valid_texts)
            
            results = []
            valid_idx = 0
            for text in processed_texts:
                if text:
                    pred = predictions[valid_idx]
                    proba = probas[valid_idx]
                    is_personal = pred == 1
                    confidence = max(proba)
                    results.append((bool(is_personal), float(confidence)))
                    valid_idx += 1
                else:
                    results.append((False, 0.0))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            return [(False, 0.0)] * len(texts)


def main():
    """Test the TF-IDF classifier."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    classifier = TFIDFClassifier()
    
    # Sample training data
    sample_data = [
        {'text': 'In my personal blog, I share my thoughts on technology and my journey as a developer.', 'is_personal': True},
        {'text': 'Our company blog features the latest industry insights and product updates.', 'is_personal': False},
        {'text': 'I started this blog to share my experiments with machine learning.', 'is_personal': True},
        {'text': 'Top 10 SEO strategies to boost your website traffic.', 'is_personal': False}
    ]
    
    if classifier.train(sample_data):
        print("✅ TF-IDF classifier trained!")
        
        test_texts = [
            "My personal journey with Python programming",
            "Best practices for enterprise software development"
        ]
        
        for text in test_texts:
            is_personal, confidence = classifier.predict(text)
            print(f"'{text[:30]}...': Personal={is_personal}, Confidence={confidence:.3f}")


if __name__ == "__main__":
    main() 