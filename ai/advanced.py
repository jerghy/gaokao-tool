import os
import json
import time
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Optional, Union, Callable, TypeVar, Generic, List, Any
from datetime import datetime, timedelta

from ai.base import AI, call_ai, build_input_content, _get_effort_value, _get_model_value

__all__ = [
    "call_ai_stream",
    "CachedAI",
    "ProgressTracker",
    "RateLimiter",
    "validate_result",
    "parse_json_result",
    "extract_markdown_code",
]

T = TypeVar('T')


def call_ai_stream(
    ai: AI,
    system_prompt: str,
    user_content: list,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    from volcenginesdkarkruntime import Ark
    
    api_key = ai.api_key or os.getenv("ARK_API_KEY", "")
    if not api_key:
        raise ValueError("API KEY未配置")
    
    client = Ark(base_url=ai.base_url, api_key=api_key, timeout=ai.timeout)
    effort = _get_effort_value(ai.reasoning_effort)
    model = _get_model_value(ai.model)
    
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": user_content}
            ],
            max_output_tokens=ai.max_output_tokens,
            reasoning={"effort": effort},
            stream=True,
        )
    except TypeError:
        full_text = ""
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
                        full_text += c.text
                        if on_chunk:
                            on_chunk(c.text)
        return full_text
    
    full_text = ""
    for event in response:
        if hasattr(event, 'delta') and event.delta:
            chunk = event.delta
            full_text += chunk
            if on_chunk:
                on_chunk(chunk)
        elif hasattr(event, 'content') and event.content:
            for c in event.content:
                if hasattr(c, 'text') and c.text:
                    chunk = c.text
                    full_text += chunk
                    if on_chunk:
                        on_chunk(chunk)
    
    return full_text


@dataclass
class CachedAI:
    ai: AI
    cache_dir: str = ".ai_cache"
    expire_seconds: Optional[int] = None
    
    def __post_init__(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, system_prompt: str, user_content: list) -> str:
        content_str = json.dumps({
            "model": _get_model_value(self.ai.model),
            "system": system_prompt,
            "user": user_content,
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _load_cache(self, key: str) -> Optional[str]:
        path = self._get_cache_path(key)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if self.expire_seconds:
                cached_time = datetime.fromisoformat(data.get("timestamp", ""))
                if datetime.now() - cached_time > timedelta(seconds=self.expire_seconds):
                    return None
            
            return data.get("result")
        except:
            return None
    
    def _save_cache(self, key: str, result: str):
        path = self._get_cache_path(key)
        data = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def call(self, system_prompt: str, user_content: list) -> str:
        key = self._get_cache_key(system_prompt, user_content)
        
        cached = self._load_cache(key)
        if cached is not None:
            return cached
        
        result = call_ai(self.ai, system_prompt, user_content)
        self._save_cache(key, result)
        return result
    
    def call_text(self, system_prompt: str, user_text: str) -> str:
        return self.call(system_prompt, build_input_content(user_text))
    
    def clear_cache(self):
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)


@dataclass
class ProgressTracker:
    progress_file: str
    _completed: set = field(default_factory=set, repr=False)
    
    def __post_init__(self):
        self.load()
    
    def load(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._completed = set(data.get("completed", []))
            except:
                self._completed = set()
        else:
            self._completed = set()
    
    def save(self):
        data = {
            "completed": list(self._completed),
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def mark_done(self, task_id: str):
        self._completed.add(str(task_id))
        self.save()
    
    def is_done(self, task_id: str) -> bool:
        return str(task_id) in self._completed
    
    def get_pending(self, all_task_ids: list) -> list:
        return [tid for tid in all_task_ids if str(tid) not in self._completed]
    
    def get_completed(self) -> list:
        return list(self._completed)
    
    def clear(self):
        self._completed = set()
        self.save()
    
    @property
    def count(self) -> int:
        return len(self._completed)


@dataclass
class RateLimiter:
    max_requests: int
    per_seconds: float
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _timestamps: list = field(default_factory=list, repr=False)
    
    def _clean_old_timestamps(self):
        now = time.time()
        cutoff = now - self.per_seconds
        self._timestamps = [ts for ts in self._timestamps if ts > cutoff]
    
    def wait_if_needed(self):
        with self._lock:
            self._clean_old_timestamps()
            
            if len(self._timestamps) >= self.max_requests:
                oldest = self._timestamps[0]
                wait_time = oldest + self.per_seconds - time.time()
                if wait_time > 0:
                    time.sleep(wait_time)
                self._clean_old_timestamps()
            
            self._timestamps.append(time.time())
    
    def acquire(self):
        self.wait_if_needed()


def validate_result(
    result: str,
    expect_json: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> Any:
    if min_length is not None and len(result) < min_length:
        raise ValueError(f"结果长度 {len(result)} 小于最小长度 {min_length}")
    
    if max_length is not None and len(result) > max_length:
        raise ValueError(f"结果长度 {len(result)} 大于最大长度 {max_length}")
    
    if expect_json:
        return parse_json_result(result)
    
    return result


def parse_json_result(result: str) -> Any:
    text = result.strip()
    
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法解析 JSON: {e}\n原始内容:\n{result[:500]}")


def extract_markdown_code(text: str, language: Optional[str] = None) -> List[str]:
    import re
    
    if language:
        pattern = rf"```{language}\s*\n(.*?)\n```"
    else:
        pattern = r"```(?:\w*)\s*\n(.*?)\n```"
    
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def extract_first_markdown_code(text: str, language: Optional[str] = None) -> Optional[str]:
    codes = extract_markdown_code(text, language)
    return codes[0] if codes else None
