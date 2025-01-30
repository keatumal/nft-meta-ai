import time

from openai import OpenAI
from typing import Dict

from src.config import get_app_config
from src.log import log

class OpenAIImageToText:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

        config = get_app_config()
        self.min_len = config.openai.get('description_min_len', 100)
        self.max_attempts = config.openai.get('max_attempts', 5)
        self.timeout = config.openai.get('error_timeout', 10)

    def get_text_from_image(self, image_base64: str, image_type: str, prompt: str) -> Dict:
        attempt_num = self.max_attempts
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': prompt},
                                {
                                    'type': 'image_url',
                                    'image_url': {'url': f'data:{image_type};base64,{image_base64}'}
                                }
                            ]
                        }
                ])
                text = response.choices[0].message.content
                if len(text) < self.min_len:
                    if attempt_num > 0:
                        attempt_num -= 1
                        log.print(f'Got a text length of {len(text)} characters')
                        log.print(f'Trying again. Attempts left: {attempt_num}')
                        continue
                    else:
                        return {
                            'error': 'Text is too short'
                        }
                
                return {
                    'response': text
                }
            except Exception as e:
                log.print(f'OpenAI API Error: {e}')
                log.print(f'Try again in {self.timeout} seconds')
                time.sleep(self.timeout)