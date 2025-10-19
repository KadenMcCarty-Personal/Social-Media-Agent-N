from services.ollama_client import OllamaClient
from services.ml_models import MLModels
from config.settings import Config

class ResponseGenerator:
    def __init__(self, db):
        self.db = db
        self.ollama = OllamaClient()
        self.ml_models = MLModels()
        
        # Build semantic index for canned responses
        canned_responses = self.db.get_all_canned_responses()
        self.ml_models.build_canned_response_index(canned_responses)
    
    def generate_response(self, post_content):
        """Main method to generate response using ML pipeline"""
        
        # Classify intent using huggingface
        intent_result = self.ml_models.classify_intent(post_content)
        intent = intent_result['intent']
        intent_confidence = intent_result['confidence']
        # Print intent and confidence in the score
        print(f"  🎯 Intent: {intent} (confidence: {intent_confidence:.2f})")
        
        # Classify sentiment using hugginface
        sentiment_result = self.ml_models.analyze_sentiment(post_content)
        sentiment = sentiment_result['sentiment']
        sentiment_confidence = sentiment_result['confidence']
        # Print sentiment and confidence in the score
        print(f"  😊 Sentiment: {sentiment} (confidence: {sentiment_confidence:.2f})")
        
        # Find a proper canned response to the post using intent 
        similar_response, similarity_score = self.ml_models.find_similar_response(post_content)
        
        print(f"  📋 Best canned match similarity: {similarity_score:.2f}")
        
        # Step 4: Decide response strategy
        if similarity_score >= Config.CANNED_RESPONSE_THRESHOLD:
            # High confidence - use canned response
            response_text = similar_response['text']
            response_type = 'canned'
            print(f"  ✅ Using canned response")
        else:
            # Low confidence - generate with Ollama
            print(f"  🤖 Generating response with Ollama...")
            
            # Provide examples to Ollama for few-shot learning
            canned_examples = similar_response['text'] if similar_response else ""
            
            response_text = self.ollama.generate_with_context(
                post_content,
                intent,
                sentiment,
                canned_examples
            )
            
            response_type = 'ai'
            
            if not response_text:
                # Fallback if Ollama fails
                response_text = "Thanks for reaching out! We'll get back to you soon. 😊"
                response_type = 'fallback'
        
        # Validate response
        response_text = self.validate_response(response_text, post_content)
        
        # Check for toxicity
        is_toxic, toxic_word = self.ml_models.check_toxicity(response_text)
        if is_toxic:
            print(f"  ⚠️ Toxic content detected: {toxic_word}. Using safe fallback.")
            response_text = "Thank you for your message. We appreciate your feedback!"
            response_type = 'safe_fallback'
        
        return {
            'text': response_text,
            'type': response_type,
            'intent': intent,
            'sentiment': sentiment,
            'confidence': intent_confidence,
            'similarity_score': similarity_score
        }
    
    def validate_response(self, response, original_post):
        """Validate and clean response"""
        # Remove potential markdown
        response = response.replace('**', '').replace('*', '')
        
        # Ensure proper length
        if len(response) > Config.MAX_RESPONSE_LENGTH:
            response = response[:Config.MAX_RESPONSE_LENGTH-3] + '...'
        
        if len(response) < Config.MIN_RESPONSE_LENGTH:
            response = f"{response} Feel free to reach out if you have more questions!"
        
        # Remove any potential hallucinations about brand details
        # (Ollama might invent details)
        if '[LINK]' not in response and 'http' in response:
            # Remove URLs that Ollama might have hallucinated
            import re
            response = re.sub(r'http\S+', '[LINK]', response)
        
        return response.strip()