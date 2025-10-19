from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import Config

class MLModels:
    def __init__(self):
        print("Loading ML models...")
        
        # Intent classification (Zero-shot)
        # use zero-shot-classification pipeline
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model=Config.HF_INTENT_MODEL,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Sentiment analysis
        # use "sentiment-analysis" pipeline
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model=Config.HF_SENTIMENT_MODEL,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Sentence embeddings for semantic similarity
        self.embedding_model = SentenceTransformer(Config.HF_EMBEDDING_MODEL)
        
        # Cache for canned response embeddings
        self.canned_intent_embeddings = None  # NEW: Embeddings of intents/keywords
        self.canned_response_embeddings = None  # NEW: Embeddings of response text (backup)
        self.canned_responses = None    
        
        print("✅ ML models loaded successfully!")
    
    # does do something!
    def classify_intent(self, text):
        """Classify the intent of the message"""
        try:
            # The hugginface pipline accepts parameters of:
            # actual text of the post
            # get the list of intents from config
            # can it assign multiple labels to one text
            # It then assigns one label to the given text
            result = self.intent_classifier(
                text,
                candidate_labels=Config.INTENT_LABELS,
                multi_label=False
            )
            # gets the first element (the most accurate and only one because of multi_label)
            return {
                'intent': result['labels'][0],
                'confidence': result['scores'][0],
                'all_scores': dict(zip(result['labels'], result['scores']))
            }
        except Exception as e:
            print(f"Intent classification error: {e}")
            return {'intent': 'general question', 'confidence': 0.5, 'all_scores': {}}
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of the message"""
        try:
            # This is very similar to the intent classifier except it uses a different model and pipeline
            result = self.sentiment_analyzer(text)[0]
            
            return {
                'sentiment': result['label'],  # POSITIVE or NEGATIVE
                'confidence': result['score']
            }
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {'sentiment': 'NEUTRAL', 'confidence': 0.5}
    # this basically takes the text and converts it to a long list of numbers where text with similar meaning have similar numbers
    def embed_text(self, text):
        """Generate embedding for text"""
        return self.embedding_model.encode(text, convert_to_numpy=True)
    
    # gets the canned responses and also their embedings
    def build_canned_response_index(self, canned_responses):
        """Build semantic index for canned responses"""
        self.canned_responses = canned_responses
    
        # OPTION 1: Embed the intent/keyword (BETTER - what you suggested!)
        intent_texts = []
        for response in canned_responses:
            # Build a descriptive text from intent and keyword
            intent = response.get('intent', '')
            keyword = response.get('keyword', '')
            category = response.get('category', '')
        
            # Combine for better matching
            # e.g., "pricing and costs, pricing, sales"
            combined = f"{intent}, {keyword}, {category}".strip(', ')
            intent_texts.append(combined)
    
        self.canned_intent_embeddings = self.embedding_model.encode(
            intent_texts, 
            convert_to_numpy=True
        )
    
    def find_similar_response(self, query_text, top_k=3, use_intent_matching=True):
        """Find most similar canned response"""
        if self.canned_intent_embeddings is None:
            return None, 0.0
        
        # Embed the customer's query
        query_embedding = self.embed_text(query_text)
        
        # Choose which embeddings to compare against
        if use_intent_matching and self.canned_intent_embeddings is not None:
            # IMPROVED: Compare against intent/keyword embeddings
            target_embeddings = self.canned_intent_embeddings
            match_type = "intent"
        else:
            # ORIGINAL: Compare against response text embeddings
            target_embeddings = self.canned_response_embeddings
            match_type = "response"
        
        # Calculate cosine similarities
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            target_embeddings
        )[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'response': self.canned_responses[idx],
                'similarity': similarities[idx],
                'match_type': match_type
            })
        
        # Return best match
        best_match = results[0]
        
        # Debug info
        if best_match['similarity'] > 0.6:
            print(f"   🎯 Best match ({match_type}): {best_match['response'].get('keyword', 'N/A')} "
                f"(similarity: {best_match['similarity']:.2f})")
        print(f"Best canned match: {best_match['response']}")
        return best_match['response'], best_match['similarity']
    
    def check_toxicity(self, text):
        # """Check if response contains toxic content (basic version)"""
        # # This is a simplified version. For production, use detoxify or similar
        # toxic_words = ['hate', 'stupid', 'idiot', 'fuck', 'shit', 'damn']
        # text_lower = text.lower()
        
        # for word in toxic_words:
        #     if word in text_lower:
        #         return True, word
        
        # ???? maybe implement later ????

        return False, None