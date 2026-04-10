import os
import json
import logging
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import (
    AI,
    ReasoningEffort,
    call_ai_json,
    build_input_content,
    parse_items_text,
    extract_image_paths_from_items,
)
from ai.batch import run_batch

logger = logging.getLogger(__name__)

__all__ = [
    "TagResult",
    "collect_all_tags",
    "generate_tags_for_question",
    "save_tags_to_json",
    "process_tags_for_question",
    "batch_process_tags",
]


@dataclass
class TagResult:
    tags: list[str]
    raw_response: str

    def to_dict(self) -> dict:
        return {"tags": self.tags}


def collect_all_tags(data_dir: str) -> list[str]:
    all_tags = set()
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            tags = data.get("tags", [])
            for tag in tags:
                if tag:
                    all_tags.add(tag)
        except Exception:
            pass
    return sorted(list(all_tags))


def load_prompt_from_file(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_tag_prompt(
    question_text: str,
    answer_text: str,
    existing_tags: list[str],
) -> str:
    prompt = f"""请为以下题目生成标签：

【题目】
{question_text}

【答案】
{answer_text if answer_text else "暂无答案"}
"""
    if existing_tags:
        prompt += f"""
【已有标签库】
{json.dumps(existing_tags, ensure_ascii=False, indent=2)}

请优先复用已有标签库中的标签，避免生成同义异构标签。
"""
    return prompt


def generate_tags_for_question(
    data_dir: str,
    question_id: str,
    prompt_path: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
    existing_tags: Optional[list[str]] = None,
) -> Optional[TagResult]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if not os.path.exists(file_path):
        logger.warning(f"题目文件不存在: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)

    image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

    if existing_tags is None:
        existing_tags = collect_all_tags(data_dir)

    system_prompt = load_prompt_from_file(prompt_path)
    user_prompt = build_tag_prompt(question_text, answer_text, existing_tags)

    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model or "doubao-seed-2-0-pro-260215",
        reasoning_effort=reasoning_effort or ReasoningEffort.medium,
        max_output_tokens=max_output_tokens or 4096,
        api_key=api_key,
    )

    user_content = build_input_content(user_prompt, image_paths)
    raw_response = call_ai_json(final_ai, system_prompt, user_content)

    if isinstance(raw_response, str):
        try:
            json_str = raw_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            result = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"AI返回内容不是有效的JSON格式:\n{raw_response}")
            return None
    else:
        result = raw_response

    tags = result.get("tags", [])
    if not isinstance(tags, list):
        logger.warning(f"AI返回的tags不是列表格式: {tags}")
        return None

    valid_tags = []
    valid_prefixes = ("知识点::", "难度::", "题型::", "能力素养::")
    for tag in tags:
        if isinstance(tag, str) and tag.startswith(valid_prefixes):
            valid_tags.append(tag)

    return TagResult(tags=valid_tags, raw_response=raw_response if isinstance(raw_response, str) else json.dumps(raw_response))


def save_tags_to_json(
    data_dir: str,
    question_id: str,
    tag_result: TagResult,
    replace: bool = False,
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if replace:
        data["tags"] = tag_result.tags
    else:
        existing_tags = data.get("tags", [])
        valid_prefixes = ("知识点::", "难度::", "题型::", "能力素养::")
        non_standard_tags = [t for t in existing_tags if not t.startswith(valid_prefixes)]
        existing_standard_tags = set(t for t in existing_tags if t.startswith(valid_prefixes))
        for tag in tag_result.tags:
            existing_standard_tags.add(tag)
        data["tags"] = non_standard_tags + list(existing_standard_tags)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_tags_for_question(
    data_dir: str,
    question_id: str,
    prompt_path: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
    replace: bool = False,
    skip_if_has_valid_tags: bool = False,
) -> Optional[TagResult]:
    if skip_if_has_valid_tags:
        file_path = os.path.join(data_dir, f"{question_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            existing_tags = data.get("tags", [])
            valid_prefixes = ("知识点::", "难度::", "题型::", "能力素养::")
            has_valid = any(t.startswith(valid_prefixes) for t in existing_tags if isinstance(t, str))
            if has_valid:
                logger.info(f"[跳过] {question_id}: 已有规范标签")
                return None

    result = generate_tags_for_question(
        data_dir=data_dir,
        question_id=question_id,
        prompt_path=prompt_path,
        ai=ai,
        api_key=api_key,
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
    )

    if result is None:
        return None

    save_tags_to_json(data_dir, question_id, result, replace=replace)
    return result


def batch_process_tags(
    data_dir: str,
    prompt_path: str,
    question_ids: Optional[list[str]] = None,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
    replace: bool = False,
    skip_if_has_valid_tags: bool = True,
    max_workers: int = 3,
) -> dict:
    if question_ids is None:
        question_ids = []
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                question_ids.append(filename[:-5])

    existing_tags = collect_all_tags(data_dir)

    def _process_one(qid):
        result = {"id": qid, "success": False, "message": ""}
        try:
            if skip_if_has_valid_tags:
                file_path = os.path.join(data_dir, f"{qid}.json")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                existing = data.get("tags", [])
                valid_prefixes = ("知识点::", "难度::", "题型::", "能力素养::")
                has_valid = any(t.startswith(valid_prefixes) for t in existing if isinstance(t, str))
                if has_valid:
                    result["message"] = "已有规范标签"
                    return result

            tag_result = generate_tags_for_question(
                data_dir=data_dir, question_id=qid, prompt_path=prompt_path,
                ai=ai, api_key=api_key, model=model,
                reasoning_effort=reasoning_effort, max_output_tokens=max_output_tokens,
                existing_tags=existing_tags,
            )
            if tag_result:
                save_tags_to_json(data_dir, qid, tag_result, replace=replace)
                result["success"] = True
                result["message"] = f"生成 {len(tag_result.tags)} 个标签"
            else:
                result["message"] = "生成失败"
        except Exception as e:
            result["message"] = str(e)[:100]
        return result

    progress = run_batch(_process_one, question_ids, max_workers=max_workers, desc="标签生成")

    return {
        "total": progress.total,
        "success": progress.success,
        "failed": progress.failed,
        "skipped": progress.skipped,
    }
