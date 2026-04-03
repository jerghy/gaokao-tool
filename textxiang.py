from volcenginesdkarkruntime import Ark
import os
import base64

# 初始化客户端
client = Ark(
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# 构建多内容整体输入：文本+图片
whole_input = [
    {"type": "text", "text": "天很蓝，海很深"},
    {
        "type": "image_url",
        "image_url": {
            "url": "https://ark-project.tos-cn-beijing.volces.com/images/view.jpeg"
        }
    }
]

# 调用多模态模型，生成整体向量（唯一1个）
response = client.multimodal_embeddings.create(
    model="doubao-embedding-vision-251215", # 必须用251215及以上版本
    input=whole_input,
    encoding_format="float",
    dimensions=2048 # 可选1024/2048，默认2048
)

# 解析响应结果
embedding = response.data.embedding
print(f"模型: {response.model}")
print(f"向量维度: {len(embedding)}")
print(f"向量前10位: {embedding[:10]}")
print(f"Token使用: {response.usage}")