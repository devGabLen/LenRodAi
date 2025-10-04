"""
Servicio de Machine Learning con TensorFlow
"""

import numpy as np
import tensorflow as tf
from sentence_transformers import SentenceTransformer
import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional, Tuple
import pickle
import os
from datetime import datetime
import re

from src.core.config import settings

class MLService:
    """Servicio de Machine Learning para procesamiento de lenguaje natural"""
    
    def __init__(self):
        self.sentence_model = None
        self.nlp = None
        self.tfidf_vectorizer = None
        self.intent_classifier = None
        self.emotion_classifier = None
        self.model_path = settings.ML_MODEL_PATH
        
        # Crear directorio de modelos si no existe
        os.makedirs(self.model_path, exist_ok=True)
    
    async def initialize(self):
        """Inicializar modelos de ML"""
        print("🤖 Inicializando modelos de ML...")
        
        # Descargar recursos de NLTK
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except:
            pass
        
        # Inicializar Sentence Transformer
        try:
            self.sentence_model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
            print("✅ Sentence Transformer inicializado")
        except Exception as e:
            print(f"⚠️ Error inicializando Sentence Transformer: {e}")
        
        # Inicializar spaCy
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ spaCy modelo español inicializado")
        except OSError:
            print("⚠️ Modelo spaCy español no encontrado, usando modelo básico")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("⚠️ Usando modelo spaCy básico")
                self.nlp = spacy.blank("es")
        
        # Inicializar TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Cargar o crear clasificadores
        await self._load_or_create_classifiers()
        
        print("✅ Servicio ML inicializado correctamente")
    
    async def _load_or_create_classifiers(self):
        """Cargar o crear clasificadores"""
        # Intentar cargar clasificador de intenciones
        intent_model_path = os.path.join(self.model_path, "intent_classifier.pkl")
        if os.path.exists(intent_model_path):
            try:
                with open(intent_model_path, 'rb') as f:
                    self.intent_classifier = pickle.load(f)
                print("✅ Clasificador de intenciones cargado")
            except:
                self.intent_classifier = None
        else:
            self.intent_classifier = None
        
        # Intentar cargar clasificador de emociones
        emotion_model_path = os.path.join(self.model_path, "emotion_classifier.pkl")
        if os.path.exists(emotion_model_path):
            try:
                with open(emotion_model_path, 'rb') as f:
                    self.emotion_classifier = pickle.load(f)
                print("✅ Clasificador de emociones cargado")
            except:
                self.emotion_classifier = None
        else:
            self.emotion_classifier = None
    
    async def analyze_context(self, message: str, 
                            conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Analizar contexto del mensaje"""
        context = {
            "intent": await self.classify_intent(message),
            "emotions": await self.analyze_emotions(message),
            "keywords": await self.extract_keywords(message),
            "entities": await self.extract_entities(message),
            "similarity": await self.calculate_similarity(message, conversation_history),
            "complexity": await self.analyze_complexity(message),
            "language": await self.detect_language(message)
        }
        
        return context
    
    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Clasificar intención del mensaje"""
        if not self.intent_classifier:
            return {"intent": "general", "confidence": 0.5}
        
        try:
            # Preprocesar texto
            processed_text = self._preprocess_text(text)
            
            # Clasificar
            prediction = self.intent_classifier.predict([processed_text])
            confidence = max(self.intent_classifier.predict_proba([processed_text])[0])
            
            return {
                "intent": prediction[0],
                "confidence": float(confidence)
            }
        except Exception as e:
            return {"intent": "general", "confidence": 0.5, "error": str(e)}
    
    async def analyze_emotions(self, text: str) -> Dict[str, Any]:
        """Analizar emociones en el texto"""
        if not self.emotion_classifier:
            return {"emotions": ["neutral"], "confidence": 0.5}
        
        try:
            processed_text = self._preprocess_text(text)
            prediction = self.emotion_classifier.predict([processed_text])
            confidence = max(self.emotion_classifier.predict_proba([processed_text])[0])
            
            return {
                "emotions": prediction[0].split(",") if "," in prediction[0] else [prediction[0]],
                "confidence": float(confidence)
            }
        except Exception as e:
            return {"emotions": ["neutral"], "confidence": 0.5, "error": str(e)}
    
    async def extract_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave usando TF-IDF"""
        try:
            if not self.tfidf_vectorizer:
                return []
            
            # Ajustar vectorizador si es necesario
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                self.tfidf_vectorizer.fit([text])
            
            # Vectorizar texto
            tfidf_matrix = self.tfidf_vectorizer.transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Obtener palabras con mayor TF-IDF
            scores = tfidf_matrix.toarray()[0]
            top_indices = np.argsort(scores)[-10:][::-1]  # Top 10
            
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            return keywords[:5]  # Top 5
            
        except Exception as e:
            return []
    
    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extraer entidades nombradas"""
        try:
            if not self.nlp:
                return []
            
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "confidence": 0.8  # spaCy no proporciona confianza por defecto
                })
            
            return entities
            
        except Exception as e:
            return []
    
    async def calculate_similarity(self, message: str, 
                                 conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Calcular similitud con mensajes anteriores"""
        if not conversation_history or not self.sentence_model:
            return {"similarity": 0.0, "most_similar": None}
        
        try:
            # Obtener embeddings
            current_embedding = self.sentence_model.encode([message])
            
            similarities = []
            for msg in conversation_history[-5:]:  # Últimos 5 mensajes
                if msg.get("user_message"):
                    hist_embedding = self.sentence_model.encode([msg["user_message"]])
                    similarity = cosine_similarity(current_embedding, hist_embedding)[0][0]
                    similarities.append({
                        "message": msg["user_message"],
                        "similarity": float(similarity)
                    })
            
            if similarities:
                most_similar = max(similarities, key=lambda x: x["similarity"])
                avg_similarity = sum(s["similarity"] for s in similarities) / len(similarities)
                
                return {
                    "similarity": float(avg_similarity),
                    "most_similar": most_similar
                }
            
            return {"similarity": 0.0, "most_similar": None}
            
        except Exception as e:
            return {"similarity": 0.0, "most_similar": None, "error": str(e)}
    
    async def analyze_complexity(self, text: str) -> Dict[str, Any]:
        """Analizar complejidad del texto"""
        try:
            # Métricas básicas
            word_count = len(text.split())
            sentence_count = len(re.split(r'[.!?]+', text))
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            # Análisis de vocabulario
            unique_words = len(set(text.lower().split()))
            vocabulary_richness = unique_words / max(word_count, 1)
            
            # Nivel de complejidad (0-1)
            complexity = min(1.0, (avg_sentence_length / 20) + (vocabulary_richness * 2))
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": avg_sentence_length,
                "vocabulary_richness": vocabulary_richness,
                "complexity_score": complexity,
                "level": self._get_complexity_level(complexity)
            }
            
        except Exception as e:
            return {"complexity_score": 0.5, "level": "medium", "error": str(e)}
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detectar idioma del texto"""
        try:
            # Análisis básico de idioma
            spanish_indicators = ["el", "la", "de", "que", "y", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al", "del", "los", "las", "una", "pero", "sus", "más", "como", "todo", "esta", "sobre", "entre", "cuando", "muy", "sin", "hasta", "desde", "está", "mi", "porque", "qué", "sólo", "han", "yo", "hay", "vez", "puede", "todos", "así", "nos", "ni", "parte", "tiene", "él", "uno", "donde", "bien", "tiempo", "mismo", "ese", "ahora", "cada", "e", "vida", "otro", "después", "te", "otros", "aunque", "esa", "esos", "estas", "me", "antes", "estado", "contra", "sí", "sino", "forma", "caso", "nada", "hacer", "general", "pero", "menos", "año", "mundo", "aquí", "manera", "tanto", "cual", "mientras", "saber", "hasta", "donde", "durante", "través", "tanto", "tanto", "tanto"]
            
            words = text.lower().split()
            spanish_word_count = sum(1 for word in words if word in spanish_indicators)
            spanish_ratio = spanish_word_count / max(len(words), 1)
            
            if spanish_ratio > 0.1:
                language = "spanish"
                confidence = min(1.0, spanish_ratio * 5)
            else:
                language = "english"
                confidence = 1.0 - spanish_ratio
            
            return {
                "language": language,
                "confidence": confidence,
                "spanish_ratio": spanish_ratio
            }
            
        except Exception as e:
            return {"language": "unknown", "confidence": 0.5, "error": str(e)}
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesar texto para ML"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales
        text = re.sub(r'[^a-zA-Záéíóúñü\s]', '', text)
        
        # Remover espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_complexity_level(self, score: float) -> str:
        """Obtener nivel de complejidad"""
        if score < 0.3:
            return "simple"
        elif score < 0.7:
            return "medium"
        else:
            return "complex"
    
    async def train_intent_classifier(self, training_data: List[Dict[str, Any]]):
        """Entrenar clasificador de intenciones"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            texts = [item["text"] for item in training_data]
            labels = [item["intent"] for item in training_data]
            
            # Preprocesar textos
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Vectorizar
            X = self.tfidf_vectorizer.fit_transform(processed_texts)
            
            # Entrenar clasificador
            self.intent_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.intent_classifier.fit(X, labels)
            
            # Guardar modelo
            model_path = os.path.join(self.model_path, "intent_classifier.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(self.intent_classifier, f)
            
            print("✅ Clasificador de intenciones entrenado y guardado")
            
        except Exception as e:
            print(f"❌ Error entrenando clasificador: {e}")
    
    async def cleanup(self):
        """Limpiar recursos"""
        # Liberar memoria de modelos
        if self.sentence_model:
            del self.sentence_model
        if self.nlp:
            del self.nlp
