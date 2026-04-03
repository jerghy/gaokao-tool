import os
import base64
import json
from dataclasses import dataclass, field
from typing import Optional, Union
from enum import Enum

from volcenginesdkarkruntime import Ark

__all__ = [
    "AIConfig",
    "AIClient",
    "ReasoningEffort",
    "encode_image_to_base64",
    "get_image_media_type",
    "extract_response_text",
    "call_ai_api",
    "build_input_content",
    "parse_items_text",
    "load_images_data",
    "get_image_path_by_config_id",
    "extract_image_paths_from_items",
]


class ReasoningEffort(Enum):
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    
    @property
    def value(self) -> str:
        return self._value_


@dataclass
class AIConfig:
    api_key: str = field(default_factory=lambda: os.getenv("ARK_API_KEY", ""))
    model: str = "doubao-seed-2-0-pro-260215"
    max_output_tokens: int = 131072
    reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high
    timeout: int = 1800
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"


class AIClient:
    _instance: Optional["AIClient"] = None
    _client: Optional[Ark] = None
    _config: AIConfig = AIConfig()

    def __new__(cls, config: Optional[AIConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[AIConfig] = None):
        if config:
            self._config = config
            self._client = None

    @property
    def client(self) -> Ark:
        if self._client is None:
            if not self._config.api_key:
                raise ValueError("API KEY未配置，请设置ARK_API_KEY环境变量或传入config")
            self._client = Ark(
                base_url=self._config.base_url,
                api_key=self._config.api_key,
                timeout=self._config.timeout,
            )
        return self._client

    @property
    def config(self) -> AIConfig:
        return self._config

    def _get_reasoning_effort(self, effort: Optional[Union[ReasoningEffort, str]]) -> str:
        if effort is None:
            effort = self._config.reasoning_effort
        if isinstance(effort, ReasoningEffort):
            return effort.value
        return effort

    def call(
        self,
        system_prompt: str,
        user_content: list[dict],
        model: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    ) -> str:
        effort = self._get_reasoning_effort(reasoning_effort)
        response = self.client.responses.create(
            model=model or self._config.model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}]
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            max_output_tokens=max_output_tokens or self._config.max_output_tokens,
            reasoning={"effort": effort},
        )
        return extract_response_text(response)


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return media_types.get(ext, "image/png")


def extract_response_text(response) -> str:
    for item in response.output:
        if hasattr(item, 'content') and item.content:
            for c in item.content:
                if hasattr(c, 'text') and c.text:
                    return c.text
    return ""


def build_input_content(
    text: str = "",
    image_paths: list[str] = None,
) -> list[dict]:
    content = []

    if image_paths:
        for image_path in image_paths:
            if os.path.exists(image_path):
                base64_image = encode_image_to_base64(image_path)
                media_type = get_image_media_type(image_path)
                content.append({
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{base64_image}"
                })

    if text:
        content.append({
            "type": "input_text",
            "text": text
        })

    return content


def call_ai_api(
    system_prompt: str,
    user_text: str = "",
    user_image_paths: list[str] = None,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> str:
    config = AIConfig(
        api_key=api_key or os.getenv("ARK_API_KEY", ""),
        model=model,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )
    client = AIClient(config)
    user_content = build_input_content(user_text, user_image_paths)
    return client.call(system_prompt, user_content)


def parse_items_text(items: list) -> str:
    """
    从 items 列表中提取文本内容
    
    Args:
        items: 题目或答案的 items 列表
    
    Returns:
        str: 拼接后的文本内容
    """
    text_parts = []
    for item in items:
        if item.get("type") in ("text", "richtext"):
            text_parts.append(item.get("content", ""))
    return "".join(text_parts)


_images_data_cache = None
_images_data_path = None


def _get_base_dir(data_dir: str) -> str:
    """
    获取项目根目录（print 目录）
    
    Args:
        data_dir: 数据目录路径（相对或绝对）
    
    Returns:
        str: 项目根目录的绝对路径
    """
    abs_data_dir = os.path.abspath(data_dir)
    return os.path.dirname(abs_data_dir)


def load_images_data(data_dir: str) -> dict:
    """
    加载 images.json 数据
    
    Args:
        data_dir: 数据目录路径
    
    Returns:
        dict: 包含 images 和 configs 的数据
    """
    global _images_data_cache, _images_data_path
    
    base_dir = _get_base_dir(data_dir)
    images_path = os.path.join(base_dir, "images.json")
    
    if _images_data_cache is not None and _images_data_path == images_path:
        return _images_data_cache
    
    if os.path.exists(images_path):
        with open(images_path, "r", encoding="utf-8") as f:
            _images_data_cache = json.load(f)
            _images_data_path = images_path
            return _images_data_cache
    
    return {"images": {}, "configs": {}}


def get_image_path_by_config_id(
    config_id: str,
    data_dir: str,
    images_data: Optional[dict] = None
) -> Optional[str]:
    """
    通过 config_id 获取图片的实际路径
    
    Args:
        config_id: 图片配置 ID
        data_dir: 数据目录路径
        images_data: images.json 数据（可选，不传则自动加载）
    
    Returns:
        str 或 None: 图片的完整路径
    """
    if images_data is None:
        images_data = load_images_data(data_dir)
    
    config = images_data.get("configs", {}).get(config_id)
    if not config:
        return None
    
    image_id = config.get("image_id")
    if not image_id:
        return None
    
    image = images_data.get("images", {}).get(image_id)
    if not image:
        return None
    
    path = image.get("path")
    if not path:
        return None
    
    base_dir = _get_base_dir(data_dir)
    full_path = os.path.normpath(os.path.join(base_dir, path))
    
    if os.path.exists(full_path):
        return full_path
    
    return None


def extract_image_paths_from_items(
    items: list,
    data_dir: str,
    images_data: Optional[dict] = None
) -> list[str]:
    """
    从 items 列表中提取所有图片路径
    
    支持两种格式：
    1. 新格式：{"type": "image", "config_id": "xxx"}
    2. 旧格式：{"type": "image", "src": "xxx"}
    
    Args:
        items: 题目或答案的 items 列表
        data_dir: 数据目录路径
        images_data: images.json 数据（可选）
    
    Returns:
        list[str]: 图片路径列表
    """
    paths = []
    
    for item in items:
        if item.get("type") != "image":
            continue
        
        config_id = item.get("config_id")
        if config_id:
            path = get_image_path_by_config_id(config_id, data_dir, images_data)
            if path:
                paths.append(path)
            continue
        
        src = item.get("src")
        if src:
            base_path = _get_base_dir(data_dir)
            full_path = os.path.normpath(os.path.join(base_path, src))
            if os.path.exists(full_path):
                paths.append(full_path)
    
    return paths
