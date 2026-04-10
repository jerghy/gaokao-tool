import os
import json
from typing import Optional, Any, Union
from dataclasses import dataclass, field

from ai.base import (
    AI,
    ReasoningEffort,
    call_ai,
    build_input_content,
    parse_items_text,
    extract_image_paths_from_items,
)
from ai.batch import run_batch
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
    "AI",
]


class AIContext:
    def __init__(
        self,
        data_dir: str,
        ai: Optional[AI] = None,
        api_base_url: str = "http://localhost:5000",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.data_dir = data_dir
        self.api_base_url = api_base_url
        
        if ai is not None:
            self._ai = ai
        else:
            self._ai = AI(
                api_key=api_key,
                model=model or "doubao-seed-2-0-pro-260215",
            )
    
    @property
    def ai(self) -> AI:
        return self._ai

    def question(self, question_id: str) -> "Question":
        return Question.load(question_id, ctx=self)

    def search(self, query: str) -> list["Question"]:
        if self.api_base_url is None:
            return self.search_local(query)
        ids = _search_questions_via_api(query, api_base_url=self.api_base_url)
        return [Question.load(qid, ctx=self) for qid in ids]

    def search_local(self, query: str = "") -> list["Question"]:
        import os
        import json
        from ai.base import parse_items_text, extract_image_paths_from_items

        all_ids = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                qid = filename[:-5]
                if not query.strip():
                    all_ids.append(qid)
                    continue
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                question_str = json.dumps(data.get('question', {}), ensure_ascii=False)
                answer_str = json.dumps(data.get('answer', {}), ensure_ascii=False)
                tags = data.get('tags', [])
                for sq in data.get('sub_questions', []):
                    tags.extend(sq.get('tags', []))
                query_lower = query.lower()
                if query_lower in question_str.lower() or query_lower in answer_str.lower() or any(query_lower in t.lower() for t in tags):
                    all_ids.append(qid)
        return [Question.load(qid, ctx=self) for qid in all_ids]

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

    def ai(
        self,
        system_prompt: str,
        output_field: Optional[str] = None,
        ai: Optional[AI] = None,
        context: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
        max_output_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> str:
        base_ai = ai or (self._ctx.ai if self._ctx else AI())
        
        final_ai = base_ai.with_overrides(
            model=model,
            reasoning_effort=reasoning_effort,
            max_output_tokens=max_output_tokens,
            api_key=api_key,
        )

        prompt_parts = []
        if self.question_text:
            prompt_parts.append(f"【题目】\n{self.question_text}")
        if self.answer_text:
            prompt_parts.append(f"【答案】\n{self.answer_text}")
        if context:
            prompt_parts.append(f"【额外上下文】\n{context}")

        user_text = "\n\n".join(prompt_parts)
        user_content = build_input_content(user_text, self.image_paths)
        
        result = call_ai(final_ai, system_prompt, user_content)

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

    @property
    def tags(self) -> list[str]:
        own_tags = self.raw_data.get("tags", [])
        sub_question_tags = []
        for sq in self.raw_data.get("sub_questions", []):
            sub_question_tags.extend(sq.get("tags", []))
        return list(set(own_tags + sub_question_tags))

    @property
    def sub_question_texts(self) -> list[str]:
        return [sq.question_text for sq in self.sub_questions]


def batch_ai(
    questions: list[Question],
    system_prompt: str,
    output_field: str = None,
    ai: Optional[AI] = None,
    max_workers: int = 3,
    **kwargs
) -> dict:
    def _process_one(q):
        entry = {"id": q.id, "success": False, "message": ""}
        try:
            if output_field and q._ctx:
                file_path = os.path.join(q._ctx.data_dir, f"{q.id}.json")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if output_field in existing and existing.get(output_field):
                        entry["message"] = "已存在"
                        return entry

            call_kwargs = {"output_field": output_field, **kwargs}
            if ai is not None:
                call_kwargs["ai"] = ai
            r = q.ai(system_prompt, **call_kwargs)
            entry["success"] = True
            entry["message"] = "处理完成"
        except Exception as e:
            entry["message"] = str(e)[:100]
        return entry

    progress = run_batch(_process_one, questions, max_workers=max_workers, desc="AI处理", item_id_fn=lambda q: q.id)

    return {
        "success": progress.success,
        "failed": progress.failed,
        "skipped": progress.skipped,
    }
