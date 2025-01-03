from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

class LLM():
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.session = None

    def send_message(self, prompt, model = 'gpt-4o-mini') -> str:
        completion = self.openai.chat.completions.create(
        model=model,
        messages=[
                {"role": "system", "content": prompt},
            ],
        response_format={"type": "json_object"}
        )

        response = completion.choices[0].message.content

        return response
    
    def send_message_for_code(self, prompt, model = 'gpt-4o-mini') -> str:
        completion = self.openai.chat.completions.create(
        model=model,
        messages=[
                {"role": "system", "content": prompt},
            ],
        response_format={"type": "text"}
        )

        response = completion.choices[0].message.content

        return response
    
    def generate_embedding(self, data):
        embd = self.openai.embeddings.create(
            model="text-embedding-3-large",
            input="The food was delicious and the waiter...",
            encoding_format="float"
            )
        return embd.data[0].embedding