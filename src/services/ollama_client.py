import ollama
from config.settings import Config

class OllamaClient:
    def __init__(self):
        self.model = Config.OLLAMA_MODEL
        self.host = Config.OLLAMA_HOST
    # parameters:
    # the users prompt (comment/post) 
    # prompt to prep system and give context
    # 
    def generate_response(self, prompt, system_prompt="", max_tokens=150, temperature=0.7):
        """Generate response using Ollama"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )
            
            return response['message']['content'].strip()
        
        except Exception as e:
            print(f"Error with Ollama: {e}")
            return None
    
    def generate_with_context(self, post_content, intent, sentiment, canned_examples=""):
        """Generate contextual response"""
        system_prompt = """You are a professional social media manager. 
Generate brief, friendly, and helpful responses to customer posts.
Keep responses under 280 characters. Be empathetic and solution-oriented.
Never make promises you can't keep. Always maintain brand voice. 
Make sure you stick closely to the canned examples and only tweak responses where necessary"""
        
        user_prompt = f"""Customer post: "{post_content}"

Intent: {intent}
Sentiment: {sentiment}

{f'Similar past responses: {canned_examples}' if canned_examples else ''}

Generate a brief, appropriate reply:"""
        
        return self.generate_response(user_prompt, system_prompt, max_tokens=100, temperature=0.7)