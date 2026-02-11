import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()


class LLMClient:
    def __init__(self):
        """
        通用大模型客户端
        使用通用三元组进行配置：
        - LLM_API_KEY     通用大模型 Key（可以是 OpenAI / DeepSeek / Moonshot 等）
        - LLM_BASE_URL    通用大模型 Base URL
        - LLM_MODEL       通用大模型名称

        约定：
        - 如果你只想用 OpenAI，则在 .env 中设置：
            LLM_API_KEY=你的OpenAIKey
            LLM_BASE_URL=https://api.openai.com/v1
            LLM_MODEL=o3-mini
          如果不设置 LLM_MODEL，则默认使用 o3-mini。
        """
        # 1) 读取通用大模型 Key
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("❌ 未找到 LLM_API_KEY，请在 .env 中配置通用大模型的 Key。")

        # 2) 读取 Base URL，未配置时默认指向 OpenAI
        self.base_url = (
            os.getenv("LLM_BASE_URL")
            or "https://api.openai.com/v1"
        )

        # 3) 读取模型名称，默认使用 o3-mini（满足“翻译调用 o3-mini”的需求）
        #    同时对环境变量做一层“白名单校验”，如果填了不支持的值（例如 GPT），则自动回落到 o3-mini，
        #    避免出现你截图里的 model_not_found 错误。
        env_model = os.getenv("LLM_MODEL")
        # 允许的模型名称列表（根据你 .env 里的注释扩展）
        allowed_models = {
            "o3-mini",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-5",
        }
        if env_model and env_model.lower() in {m.lower() for m in allowed_models}:
            # 如果用户配置在白名单中，就按用户配置来（大小写不敏感）
            # 为保持与接口一致，这里再从 allowed_models 中找出规范写法
            for m in allowed_models:
                if env_model.lower() == m.lower():
                    self.model = m
                    break
        else:
            # 否则一律回落为 o3-mini
            self.model = "o3-mini"

        # 【关键】针对某些国内转发服务，设置直连白名单
        if self.base_url and ("deepseek" in self.base_url or "moonshot" in self.base_url):
            os.environ["NO_PROXY"] = "api.deepseek.com,api.moonshot.cn"

        # 4) 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def get_completion(self, prompt, system_prompt="You are a helpful assistant"):
        """
        基础对话功能
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                temperature=1.3
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return f"Error: {e}"

    def explain_term_in_context(self, term, context):
        """
        解析功能：返回 JSON 格式 (包含翻译和解释)
        """
        # 1. 构造 Prompt，强制 AI 返回 JSON
        prompt = f"""
        任务：
        1. 将句子 "{context}" 翻译成通顺的简体中文。
        2. 结合该语境，详细解释单词 "{term}" 的含义。

        【重要】请务必只返回一个纯 JSON 格式的数据，不要包含 markdown 标记或额外文字。格式如下：
        {{
            "translation": "这里填句子的中文翻译",
            "explanation": "这里填单词的中文解释"
        }}
        """

        # 2. 获取 AI 回复
        raw_content = self.get_completion(prompt, system_prompt="你是一个输出 JSON 格式的 API 助手。")

        # 3. 解析 JSON
        try:
            match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if match:
                json_str = match.group()
                return json.loads(json_str)
            else:
                return {
                    "translation": raw_content,
                    "explanation": "AI 未按 JSON 格式返回，请重试。"
                }
        except Exception as e:
            print(f"⚠️ JSON 解析失败: {e}")
            return {
                "translation": raw_content,
                "explanation": "解析出错"
            }

    def translate(self, text, target_lang="中文"):
        prompt = f"请将以下内容翻译成{target_lang}：\n\n{text}"
        return self.get_completion(prompt, system_prompt="你是一个精通多国语言的专业翻译家。")


# 自测代码
if __name__ == "__main__":
    try:
        bot = LLMClient()
        print("✅ LLMClient 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")