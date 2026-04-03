import os
import json
from typing import Optional, Any, Union
from dataclasses import dataclass, field

from ai.base import (
    AIConfig,
    AIClient,
    ReasoningEffort,
    build_input_content,
    parse_items_text,
    extract_image_paths_from_items,
)
from ai.generic_processor import (
    search_questions_via_api as _search_questions_via_api,
    process_with_generic_ai,
    save_generic_results,
    GenericAIResult,
)

__all__ = [
    "AIContext",
    "Question",
    "batch_ai",
    "ReasoningEffort",
]


class AIContext:
    def __init__(self, data_dir: str, api_key: Optional[str] = None, model: str = "doubao-seed-2-0-pro-260215", api_base_url: str = "http://localhost:5000"):
        self.data_dir = data_dir
        self._config = AIConfig(
            api_key=api_key or os.getenv("ARK_API_KEY", ""),
            model=model,
        )
        self.api_base_url = api_base_url

    @property
    def config(self) -> AIConfig:
        return self._config

    def question(self, question_id: str) -> "Question":
        return Question.load(question_id, ctx=self)

    def search(self, query: str) -> list["Question"]:
        ids = _search_questions_via_api(query, api_base_url=self.api_base_url)
        return [Question.load(qid, ctx=self) for qid in ids]

    def search_questions(self, query: str) -> list["Question"]:
        return self.search(query)


class Question:
    def __init__(
        self,
        id: str,
        question_text: str = "",
        answer_text: str = "",
        image_paths: Optional[list[str]] = None,
        sub_questions: Optional[list["Question"]] = None,
        raw_data: Optional[dict] = None,
        _ctx: Optional[AIContext] = None,
    ):
        self.id = id
        self.question_text = question_text
        self.answer_text = answer_text
        self.image_paths = image_paths or []
        self.sub_questions = sub_questions or []
        self.raw_data = raw_data or {}
        self._ctx = _ctx
        self._last_ai_result: Optional[str] = None

    @staticmethod
    def load(question_id: str, ctx: AIContext = None) -> "Question":
        if ctx is not None:
            data_dir = ctx.data_dir
        else:
            raise ValueError("ctx is required to load a question")

        file_path = os.path.join(data_dir, f"{question_id}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Question file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        question_items = raw_data.get("question", {}).get("items", [])
        answer_items = raw_data.get("answer", {}).get("items", [])

        question_text = parse_items_text(question_items)
        answer_text = parse_items_text(answer_items)
        image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

        sub_questions_raw = raw_data.get("sub_questions", [])
        sub_questions = []
        for subq in sub_questions_raw:
            subq_items = subq.get("question_text", {}).get("items", [])
            subq_text = parse_items_text(subq_items)
            subq_images = extract_image_paths_from_items(subq_items, data_dir)
            sub_questions.append(Question(
                id=str(subq.get("id", "")),
                question_text=subq_text,
                answer_text=answer_text,
                image_paths=subq_images if subq_images else image_paths,
                raw_data=subq,
                _ctx=ctx,
            ))

        return Question(
            id=question_id,
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths,
            sub_questions=sub_questions,
            raw_data=raw_data,
            _ctx=ctx,
        )

    def ai(self, system_prompt: str, output_field: Optional[str] = None, **kwargs) -> str:
        extra_context = kwargs.pop("context", None)
        api_key = kwargs.pop("api_key", None)
        model = kwargs.pop("model", None)
        max_output_tokens = kwargs.pop("max_output_tokens", 131072)
        reasoning_effort = kwargs.pop("reasoning_effort", ReasoningEffort.high)

        prompt_parts = []
        if self.question_text:
            prompt_parts.append(f"【题目】\n{self.question_text}")
        if self.answer_text:
            prompt_parts.append(f"【答案】\n{self.answer_text}")
        if extra_context:
            prompt_parts.append(f"【额外上下文】\n{extra_context}")

        user_text = "\n\n".join(prompt_parts)

        config = AIConfig(
            api_key=api_key or (self._ctx.config.api_key if self._ctx else os.getenv("ARK_API_KEY", "")),
            model=model or (self._ctx.config.model if self._ctx else "doubao-seed-2-0-pro-260215"),
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )
        client = AIClient(config)
        user_content = build_input_content(user_text, self.image_paths)
        result = client.call(system_prompt, user_content)

        self._last_ai_result = result

        if output_field and self._ctx:
            self.save(output_field, result)

        return result

    def process(self, system_prompt: str, output_field: str, **kwargs) -> list:
        tags = kwargs.pop("tags", None)
        require_all = kwargs.pop("require_all", False)
        enable_sub_filter = tags is not None

        if not self._ctx:
            raise ValueError("Question requires an AIContext to call process()")

        results = process_with_generic_ai(
            data_dir=self._ctx.data_dir,
            question_id=self.id,
            system_prompt=system_prompt,
            output_field=output_field,
            sub_question_tags=tags,
            require_all_sub_tags=require_all,
            enable_sub_question_filter=enable_sub_filter,
            **kwargs,
        )
        return results

    def save(self, field: str, result: Any = None):
        if result is None:
            result = self._last_ai_result
        if result is None:
            raise ValueError("No result to save. Call ai() first or pass result explicitly.")

        if not self._ctx:
            raise ValueError("Question requires an AIContext to save results")

        file_path = os.path.join(self._ctx.data_dir, f"{self.id}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Question file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data[field] = result

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @property
    def subs(self) -> list["Question"]:
        return self.sub_questions

    def filter_sub(self, tags: Optional[list[str]] = None, require_all: bool = False) -> list["Question"]:
        if not tags:
            return self.sub_questions

        filtered = []
        for subq in self.sub_questions:
            subq_tags = subq.raw_data.get("tags", [])
            if require_all:
                if all(tag in subq_tags for tag in tags):
                    filtered.append(subq)
            else:
                if any(tag in subq_tags for tag in tags):
                    filtered.append(subq)
        return filtered


def batch_ai(questions: list[Question], system_prompt: str, output_field: str = None, max_workers: int = 3, **kwargs) -> dict:
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print_lock = threading.Lock()
    results = {"success": [], "failed": [], "skipped": []}
    total = len(questions)

    print(f"共 {total} 个题目需要处理")
    if output_field:
        print(f"输出字段: {output_field}")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    def _process_one(q: Question, index: int) -> dict:
        entry = {"id": q.id, "success": False, "message": ""}
        try:
            if output_field and q._ctx:
                file_path = os.path.join(q._ctx.data_dir, f"{q.id}.json")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if output_field in existing and existing.get(output_field):
                        entry["message"] = "已存在"
                        with print_lock:
                            print(f"[{index}/{total}] ~ {q.id}: 已存在，跳过")
                        return entry

            r = q.ai(system_prompt, output_field=output_field, **kwargs)
            entry["success"] = True
            entry["message"] = "处理完成"
            with print_lock:
                print(f"[{index}/{total}] ✓ {q.id}: 处理完成")
        except Exception as e:
            entry["message"] = str(e)[:100]
            with print_lock:
                print(f"[{index}/{total}] ✗ {q.id}: {entry['message']}")
        return entry

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_one, q, i): q.id
            for i, q in enumerate(questions, 1)
        }
        for future in as_completed(futures):
            entry = future.result()
            if entry["success"]:
                results["success"].append(entry["id"])
            elif entry["message"] == "已存在":
                results["skipped"].append(entry["id"])
            else:
                results["failed"].append({"id": entry["id"], "reason": entry["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, 跳过 {len(results['skipped'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason']}")

    return results
