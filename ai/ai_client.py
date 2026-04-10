import os
import json
import time
import threading
from dataclasses import dataclass
from typing import Optional, Union, TypeVar, Generic, List, Callable
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from volcenginesdkarkruntime import Ark

from ai.content import build_input_content

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
    "_get_effort_value",
    "_get_model_value",
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
    doubao_1_5_vision_pro_32k_250115 = "doubao-1-5-vision-pro-32k-250115"
    
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
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    
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
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
    ) -> "AI":
        return AI(
            model=model or self.model,
            reasoning_effort=reasoning_effort or self.reasoning_effort,
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            api_key=api_key or self.api_key,
            timeout=self.timeout,
            base_url=self.base_url,
            temperature=temperature if temperature is not None else self.temperature,
            top_p=top_p if top_p is not None else self.top_p,
            frequency_penalty=frequency_penalty if frequency_penalty is not None else self.frequency_penalty,
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
    model = _get_model_value(ai.model)
    
    is_seed_model = "seed" in model.lower()
    
    kwargs = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": user_content}
        ],
    }
    
    if is_seed_model:
        effort = _get_effort_value(ai.reasoning_effort)
        kwargs["max_output_tokens"] = ai.max_output_tokens
        kwargs["reasoning"] = {"effort": effort}
        if ai.temperature is not None:
            kwargs["temperature"] = ai.temperature
        if ai.top_p is not None:
            kwargs["top_p"] = ai.top_p
    else:
        if ai.temperature is not None:
            kwargs["temperature"] = ai.temperature
        if ai.top_p is not None:
            kwargs["top_p"] = ai.top_p
        if ai.frequency_penalty is not None:
            kwargs["frequency_penalty"] = ai.frequency_penalty
        if ai.max_output_tokens:
            kwargs["max_tokens"] = ai.max_output_tokens
    
    response = client.responses.create(**kwargs)
    
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
    model = _get_model_value(ai.model)
    
    is_seed_model = "seed" in model.lower()
    
    kwargs = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": user_content}
        ],
        "text": {"format": {"type": "json_object"}},
    }
    
    if is_seed_model:
        effort = _get_effort_value(ai.reasoning_effort)
        kwargs["max_output_tokens"] = ai.max_output_tokens
        kwargs["reasoning"] = {"effort": effort}
        if ai.temperature is not None:
            kwargs["temperature"] = ai.temperature
        if ai.top_p is not None:
            kwargs["top_p"] = ai.top_p
    else:
        if ai.temperature is not None:
            kwargs["temperature"] = ai.temperature
        if ai.top_p is not None:
            kwargs["top_p"] = ai.top_p
        if ai.frequency_penalty is not None:
            kwargs["frequency_penalty"] = ai.frequency_penalty
        if ai.max_output_tokens:
            kwargs["max_tokens"] = ai.max_output_tokens
    
    response = client.responses.create(**kwargs)
    
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
