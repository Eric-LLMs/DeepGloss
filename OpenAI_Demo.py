import os
import openai
from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables from .env
load_dotenv()

# VPN/代理问题 如果你使用“global VPN 模式”，可能所有流量都走了 VPN，而 Python 的 HTTP 客户Session可能未正确绕过代理。
# 建议设置环境变量 NO_PROXY 来让针对 api.openai.com 的请求直接走本地网络，而不经过代理，这样可以避免代理服务器在连接上产生额外干扰
os.environ['NO_PROXY'] = 'api.deepseek.com'

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('DEEP_SEEK_API_KEY')

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)