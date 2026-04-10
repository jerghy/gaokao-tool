import os
import json
import logging
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import AI, ReasoningEffort, call_ai, build_input_content, parse_items_text, extract_image_paths_from_items
from ai.thinking_process_prompt import get_thinking_process_prompt
from ai.batch import run_batch

logger = logging.getLogger(__name__)

__all__ = [
    "ThinkingProcess",
    "ThinkingTarget",
    "generate_thinking_process",
    "generate_thinking_process_for_targets",
    "save_thinking_process_to_json",
    "batch_process_with_search",
]


@dataclass
class ThinkingTarget:
    target_id: str
    target_label: str
    question_text: str
    answer_text: str
    image_paths: list[str]


@dataclass
class ThinkingProcess:
    target_id: str
    target_label: str
    thinking_content: str
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_label": self.target_label,
            "thinking_content": self.thinking_content,
        }


def build_thinking_prompt(
    question_text: str,
    answer_text: str,
    target_label: str = "整个题目"
) -> str:
    if target_label == "整个题目":
        prompt = f"""请对以下题目进行全维度思考过程还原：

原题：{question_text}

答案：{answer_text}

请严格按照系统提示词中的格式要求，输出完整的思考过程。"""
    else:
        prompt = f"""请对以下题目的部分内容进行全维度思考过程还原：

原题：{question_text}

答案：{answer_text}

需要生成思考过程的部分：{target_label}

请严格按照系统提示词中的格式要求，输出完整的思考过程。"""
    return prompt


def generate_thinking_process(
    question_text: str,
    answer_text: str,
    image_paths: list[str],
    target_label: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
) -> ThinkingProcess:
    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    prompt_text = build_thinking_prompt(question_text, answer_text, target_label)
    user_content = build_input_content(prompt_text, image_paths)
    raw_response = call_ai(final_ai, get_thinking_process_prompt(), user_content)

    return ThinkingProcess(
        target_id="",
        target_label=target_label,
        thinking_content=raw_response,
        raw_response=raw_response
    )


def extract_thinking_targets(
    data_dir: str,
    question_id: str,
    data: Optional[dict] = None
) -> list[ThinkingTarget]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if data is None:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    own_tags = data.get("tags", [])
    sub_question_tags = []
    for sq in data.get("sub_questions", []):
        sub_question_tags.extend(sq.get("tags", []))
    tags = list(set(own_tags + sub_question_tags))

    if "思维" not in tags:
        return []

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)

    image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

    sub_questions = data.get("sub_questions", [])

    targets = []

    has_subquestion_with_tag = any(
        "思维" in subq.get("tags", [])
        for subq in sub_questions
    )

    if sub_questions and has_subquestion_with_tag:
        for subq in sub_questions:
            if "思维" in subq.get("tags", []):
                subq_text_items = subq.get("question_text", {}).get("items", [])
                subq_text = parse_items_text(subq_text_items)

                subq_images = extract_image_paths_from_items(subq_text_items, data_dir)

                targets.append(ThinkingTarget(
                    target_id=str(subq.get("id", "")),
                    target_label=subq.get("title", "小问"),
                    question_text=subq_text,
                    answer_text=answer_text,
                    image_paths=subq_images
                ))
    else:
        targets.append(ThinkingTarget(
            target_id="full",
            target_label="整个题目",
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths
        ))

    return targets


def generate_thinking_process_for_targets(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> list[ThinkingProcess]:
    targets = extract_thinking_targets(data_dir, question_id)

    if not targets:
        return []

    results = []
    for target in targets:
        process = generate_thinking_process(
            question_text=target.question_text,
            answer_text=target.answer_text,
            image_paths=target.image_paths,
            target_label=target.target_label,
            api_key=api_key,
            model=model
        )
        process.target_id = target.target_id
        results.append(process)

    return results


def save_thinking_process_to_json(
    data_dir: str,
    question_id: str,
    processes: list[ThinkingProcess]
) -> bool:
    if not processes:
        return False

    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "thinking_processes" not in data:
        data["thinking_processes"] = []

    for process in processes:
        data["thinking_processes"].append(process.to_dict())

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_question_with_thinking_tag(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> list[ThinkingProcess]:
    processes = generate_thinking_process_for_targets(
        data_dir, question_id, api_key, model
    )

    if processes:
        save_thinking_process_to_json(data_dir, question_id, processes)

    return processes


def _process_single_thinking_core(data_dir, qid, api_key, model):
    result = {"id": qid, "success": False, "message": ""}
    try:
        file_path = os.path.join(data_dir, f"{qid}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing_processes = data.get("thinking_processes", [])
        if existing_processes:
            result["message"] = "already_exists"
            return result
        targets = extract_thinking_targets(data_dir, qid, data)
        if not targets:
            result["message"] = "no_thinking_tag"
            return result
        processes = generate_thinking_process_for_targets(data_dir, qid, api_key, model)
        if processes:
            save_thinking_process_to_json(data_dir, qid, processes)
            result["success"] = True
            result["message"] = "success"
        else:
            result["message"] = "no_targets"
    except Exception as e:
        result["message"] = str(e)[:100]
    return result


def batch_process_with_search(
    data_dir: str,
    question_ids: list[str],
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_workers: int = 3
) -> dict:
    def _process_one(qid):
        return _process_single_thinking_core(data_dir, qid, api_key, model)

    progress = run_batch(_process_one, question_ids, max_workers=max_workers, desc="思维过程生成")

    results = {
        "total_searched": progress.total,
        "success": progress.success,
        "failed": progress.failed,
        "skipped_no_thinking_tag": [],
        "skipped_already_exists": []
    }

    for item in progress.skipped:
        results["skipped_no_thinking_tag"].append(item)

    return results
