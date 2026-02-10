from openai import OpenAI
import os
import json
import config  # 导入 config

class LLMClient:
    def __init__(self):
        api_key = os.getenv("DEEP_SEEK_API_KEY")
        # 👇 关键修改：传入 base_url
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.OPENAI_BASE_URL  # 使用转发地址
            )
        else:
            self.client = None

    def explain_term_in_context(self, term, sentence):
        """
        解释单词在特定句子中的含义，并翻译句子。
        """
        if not self.client:
            return None

        prompt = f"""
        Context: "{sentence}"
        Term: "{term}"

        Task:
        1. Translate the sentence into Chinese.
        2. Explain the meaning of the term "{term}" specifically as it is used in this context (in Chinese).

        Return strictly JSON format:
        {{
            "translation": "中文翻译...",
            "explanation": "单词解释..."
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None