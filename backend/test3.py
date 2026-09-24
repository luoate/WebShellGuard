import dashscope
from dashscope import Generation

dashscope.api_key = "sk-db49a68955a54095af3b11ced9d3fe25"
response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "你好，通义千问！"}]
)
print(response.output.text)
