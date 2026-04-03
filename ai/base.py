import os
import base64
import json
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Union, Callable, TypeVar, Generic, List
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from volcenginesdkarkruntime import Ark

__all__ = [
    "AI",
    "Model",
    "ReasoningEffort",
    "BatchResult",
    "call_ai",
    "call_ai_text",
    "call_ai_json",
    "call_ai_with_images",
    "call_ai_with_retry",
    "call_ai_batch",
    "call_ai_batch_texts",
    "call_ai_batch_texts_safe",
    "parallel_map",
    "parallel_map_safe",
    "encode_image_to_base64",
    "get_image_media_type",
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


class Model(Enum):
    doubao_seed_2_0_pro_260215 = "doubao-seed-2-0-pro-260215"
    doubao_seed_2_0_lite_260215 = "doubao-seed-2-0-lite-260215"
    doubao_seed_2_0_mini_260215 = "doubao-seed-2-0-mini-260215"
    doubao_seed_1_6_pro_251015 = "doubao-seed-1-6-pro-251015"
    doubao_seed_1_6_lite_251015 = "doubao-seed-1-6-lite-251015"
    doubao_pro_256k = "doubao-pro-256k"
    doubao_pro_32k = "doubao-pro-32k"
    doubao_lite_32k = "doubao-lite-32k"
    
    @property
    def value(self) -> str:
        return self._value_


@dataclass
class AI:
    model: Union[Model, str] = Model.doubao_seed_2_0_pro_260215
    reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high
    max_output_tokens: int = 131072
    api_key: Optional[str] = None
    timeout: int = 1800
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    @classmethod
    def fast(cls) -> "AI":
        return cls(reasoning_effort=ReasoningEffort.low, max_output_tokens=32768)
    
    @classmethod
    def think(cls) -> "AI":
        return cls(reasoning_effort=ReasoningEffort.high, max_output_tokens=131072)
    
    @classmethod
    def deep(cls) -> "AI":
        return cls(reasoning_effort=ReasoningEffort.high, max_output_tokens=262144)
    
    def with_overrides(
        self,
        model: Optional[str] = None,
        reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
        max_output_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> "AI":
        return AI(
            model=model or self.model,
            reasoning_effort=reasoning_effort or self.reasoning_effort,
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            api_key=api_key or self.api_key,
            timeout=self.timeout,
            base_url=self.base_url,
        )


T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchResult(Generic[R]):
    index: int
    success: bool
    result: Optional[R] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "success": self.success,
            "result": self.result,
            "error": self.error,
        }


def _get_effort_value(effort: Union[ReasoningEffort, str]) -> str:
    if isinstance(effort, ReasoningEffort):
        return effort.value
    return effort


def _get_model_value(model: Union[Model, str]) -> str:
    if isinstance(model, Model):
        return model.value
    return model


def call_ai(ai: AI, system_prompt: str, user_content: list) -> str:
    api_key = ai.api_key or os.getenv("ARK_API_KEY", "")
    if not api_key:
        raise ValueError("API KEY未配置")
    
    client = Ark(base_url=ai.base_url, api_key=api_key, timeout=ai.timeout)
    effort = _get_effort_value(ai.reasoning_effort)
    model = _get_model_value(ai.model)
    
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": user_content}
        ],
        max_output_tokens=ai.max_output_tokens,
        reasoning={"effort": effort},
    )
    
    for item in response.output:
        if hasattr(item, 'content') and item.content:
            for c in item.content:
                if hasattr(c, 'text') and c.text:
                    return c.text
    return ""


def call_ai_json(
    ai: AI,
    system_prompt: str,
    user_content: list,
    auto_parse: bool = True,
) -> Union[dict, str]:
    api_key = ai.api_key or os.getenv("ARK_API_KEY", "")
    if not api_key:
        raise ValueError("API KEY未配置")
    
    client = Ark(base_url=ai.base_url, api_key=api_key, timeout=ai.timeout)
    effort = _get_effort_value(ai.reasoning_effort)
    model = _get_model_value(ai.model)
    
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": user_content}
        ],
        max_output_tokens=ai.max_output_tokens,
        reasoning={"effort": effort},
        text={"format": {"type": "json_object"}},
    )
    
    text_result = ""
    for item in response.output:
        if hasattr(item, 'content') and item.content:
            for c in item.content:
                if hasattr(c, 'text') and c.text:
                    text_result = c.text
                    break
    
    if not auto_parse:
        return text_result
    
    try:
        return json.loads(text_result)
    except json.JSONDecodeError:
        return text_result


def call_ai_text(ai: AI, system_prompt: str, user_text: str) -> str:
    return call_ai(ai, system_prompt, build_input_content(user_text))


def call_ai_with_images(ai: AI, system_prompt: str, user_text: str, image_paths: list) -> str:
    return call_ai(ai, system_prompt, build_input_content(user_text, image_paths))


def call_ai_with_retry(ai: AI, system_prompt: str, user_content: list, max_retries: int = 3, retry_delay: float = 1.0) -> str:
    last_error = None
    for attempt in range(max_retries):
        try:
            return call_ai(ai, system_prompt, user_content)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
    raise last_error


def call_ai_batch(tasks: list, ai: AI, max_workers: int = 3, on_progress=None) -> list:
    results = []
    total = len(tasks)
    print_lock = threading.Lock()
    completed = [0]

    def _call_one(task, index):
        task_id = task.get("id", str(index))
        try:
            result = call_ai(ai, task.get("system_prompt", ""), task.get("user_content", []))
            success = True
        except Exception as e:
            result = str(e)
            success = False
        
        with print_lock:
            completed[0] += 1
            if on_progress:
                on_progress(completed[0], total, task_id)
        
        return {"id": task_id, "success": success, "result": result}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_call_one, task, i): task.get("id", str(i)) for i, task in enumerate(tasks)}
        results_map = {}
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                result = future.result()
                results_map[result["id"]] = result
            except Exception as e:
                results_map[task_id] = {"id": task_id, "success": False, "result": str(e)}

    for task in tasks:
        task_id = task.get("id", str(tasks.index(task)))
        if task_id in results_map:
            results.append(results_map[task_id])

    return results


def call_ai_batch_texts(ai: AI, system_prompt: str, texts: list, max_workers: int = 3, on_progress=None) -> list:
    return parallel_map(lambda text: call_ai_text(ai, system_prompt, text), texts, max_workers=max_workers, on_progress=on_progress)


def call_ai_batch_texts_safe(ai: AI, system_prompt: str, texts: list, max_workers: int = 3, on_progress=None) -> List[BatchResult]:
    return parallel_map_safe(lambda text: call_ai_text(ai, system_prompt, text), texts, max_workers=max_workers, on_progress=on_progress)


def parallel_map(func, items, max_workers: int = 3, on_progress=None):
    results = [None] * len(items)
    print_lock = threading.Lock()
    completed = [0]

    def _process_one(item, index):
        result = func(item)
        with print_lock:
            completed[0] += 1
            if on_progress:
                on_progress(completed[0], len(items))
        return index, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, item, i): i for i, item in enumerate(items)}
        for future in as_completed(futures):
            try:
                index, result = future.result()
                results[index] = result
            except Exception as e:
                index = futures[future]
                results[index] = e

    return results


def parallel_map_safe(func, items, max_workers: int = 3, on_progress=None) -> List[BatchResult]:
    results = []
    print_lock = threading.Lock()
    completed = [0]
    total = len(items)

    def _process_one(item, index):
        try:
            result = func(item)
            return BatchResult(index=index, success=True, result=result, error=None)
        except Exception as e:
            return BatchResult(index=index, success=False, result=None, error=str(e))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, item, i): i for i, item in enumerate(items)}
        results_map = {}
        for future in as_completed(futures):
            index = futures[future]
            try:
                batch_result = future.result()
                results_map[index] = batch_result
            except Exception as e:
                results_map[index] = BatchResult(index=index, success=False, result=None, error=str(e))

    for i in range(len(items)):
        if i in results_map:
            results.append(results_map[i])

    return results


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    return media_types.get(ext, "image/png")


def build_input_content(text: str = "", image_paths: list = None) -> list:
    content = []
    if image_paths:
        for image_path in image_paths:
            if os.path.exists(image_path):
                b64 = encode_image_to_base64(image_path)
                mt = get_image_media_type(image_path)
                content.append({"type": "input_image", "image_url": "data:" + mt + ";base64," + b64})
    if text:
        content.append({"type": "input_text", "text": text})
    return content


def parse_items_text(items: list) -> str:
    return "".join(item.get("content", "") for item in items if item.get("type") in ("text", "richtext"))


_images_data_cache = None
_images_data_path = None

def _get_base_dir(data_dir: str) -> str:
    return os.path.dirname(os.path.abspath(data_dir))

def load_images_data(data_dir: str) -> dict:
    global _images_data_cache, _images_data_path
    images_path = os.path.join(_get_base_dir(data_dir), "images.json")
    if _images_data_cache is not None and _images_data_path == images_path:
        return _images_data_cache
    if os.path.exists(images_path):
        with open(images_path, "r", encoding="utf-8") as f:
            _images_data_cache = json.load(f)
            _images_data_path = images_path
            return _images_data_cache
    return {"images": {}, "configs": {}}

def get_image_path_by_config_id(config_id: str, data_dir: str, images_data=None) -> Optional[str]:
    if images_data is None:
        images_data = load_images_data(data_dir)
    config = images_data.get("configs", {}).get(config_id)
    if not config:
        return None
    image = images_data.get("images", {}).get(config.get("image_id"))
    if not image:
        return None
    path = image.get("path")
    if not path:
        return None
    full_path = os.path.normpath(os.path.join(_get_base_dir(data_dir), path))
    return full_path if os.path.exists(full_path) else None

def extract_image_paths_from_items(items: list, data_dir: str, images_data=None) -> list:
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
            full_path = os.path.normpath(os.path.join(_get_base_dir(data_dir), src))
            if os.path.exists(full_path):
                paths.append(full_path)
    return paths
