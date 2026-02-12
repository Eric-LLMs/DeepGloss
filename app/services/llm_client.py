from openai import OpenAI
import json
import config


class LLMClient:
    def __init__(self):
        # Initialize client with unified LLM_API_KEY and LLM_BASE_URL
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL

    def get_completion(self, prompt, system_prompt="You are a helpful assistant."):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Error: {e}"

    def explain_term_in_context(self, term, context_sentence):
        """
        Returns JSON: {'translation': '...', 'explanation': '...'}
        """
        # ✅ 修正 Prompt：明确要求翻译 "Entire Sentence" 而不是 "Target Term"
        system_prompt = (
            "You are a linguistic expert helper. "
            "Please perform two tasks:\n"
            "1. **Translate the entire context sentence** into natural, fluent Chinese.\n"
            "2. Provide a concise explanation of the **target term's** specific meaning/usage within this context (in English).\n\n"
            "Output strictly in JSON format with keys:\n"
            "- 'translation': The full Chinese translation of the sentence.\n"
            "- 'explanation': The explanation of the term."
        )
        user_prompt = f"Target Term: {term}\nContext Sentence: {context_sentence}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM JSON Error: {e}")
            # Fallback for error visibility
            return {"translation": "Error parsing AI response.", "explanation": str(e)}