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
    "ChineseModernTextResult",
    "get_chinese_modern_text_prompt",
    "generate_chinese_modern_text_training",
    "process_chinese_modern_text_question",
    "batch_process_chinese_modern_text",
    "get_chinese_questions_without_training",
]

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "tsc", "语文现代文.txt")


@dataclass
class ChineseModernTextResult:
    question_id: str
    training_items: list
    success: bool = True
    error: Optional[str] = None
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "training_items": self.training_items,
            "success": self.success,
            "error": self.error,
        }


def get_chinese_modern_text_prompt() -> str:
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(f"提示词文件不存在: {PROMPT_PATH}")
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _load_question_data(data_dir: str, question_id: str) -> tuple[dict, str, str, list[str]]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"题目文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)
    image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

    return data, question_text, answer_text, image_paths


def generate_chinese_modern_text_training(
    question_text: str,
    answer_text: str,
    image_paths: list[str],
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
) -> list:
    base_ai = ai or AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
    )
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    prompt_text = f"""请对以下语文现代文阅读题目进行能力点拆分训练：

【题目】
{question_text}

【答案】
{answer_text if answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""

    user_content = build_input_content(prompt_text, image_paths)
    system_prompt = get_chinese_modern_text_prompt()
    
    raw_response = call_ai_json(final_ai, system_prompt, user_content, auto_parse=False)

    if isinstance(raw_response, str):
        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI返回内容不是有效的JSON格式:\n{raw_response[:500]}") from e
    else:
        result = raw_response

    if not isinstance(result, list):
        raise ValueError("AI返回内容不是JSON数组格式")

    return result


def process_chinese_modern_text_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
    skip_if_exists: bool = True,
    output_field: str = "chinese_modern_text_training",
) -> ChineseModernTextResult:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return ChineseModernTextResult(
            question_id=question_id,
            training_items=[],
            success=False,
            error=f"题目文件不存在: {file_path}",
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tags = data.get("tags", [])
    if "语文" not in tags:
        return ChineseModernTextResult(
            question_id=question_id,
            training_items=[],
            success=False,
            error="题目标签不包含语文",
        )

    if skip_if_exists and output_field in data:
        existing = data.get(output_field, [])
        if existing:
            return ChineseModernTextResult(
                question_id=question_id,
                training_items=[],
                success=True,
                error="已存在处理结果",
            )

    try:
        _, question_text, answer_text, image_paths = _load_question_data(data_dir, question_id)

        if not question_text.strip():
            return ChineseModernTextResult(
                question_id=question_id,
                training_items=[],
                success=False,
                error="题目内容为空",
            )

        training_items = generate_chinese_modern_text_training(
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths,
            ai=ai,
            api_key=api_key,
            model=model,
            reasoning_effort=reasoning_effort,
            max_output_tokens=max_output_tokens,
        )

        _save_result(data_dir, question_id, training_items, output_field)

        return ChineseModernTextResult(
            question_id=question_id,
            training_items=training_items,
            success=True,
        )

    except Exception as e:
        logger.error(f"处理题目 {question_id} 时出错: {e}")
        return ChineseModernTextResult(
            question_id=question_id,
            training_items=[],
            success=False,
            error=str(e),
        )


def _save_result(
    data_dir: str,
    question_id: str,
    training_items: list,
    output_field: str,
) -> bool:
    if not training_items:
        return False

    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data[output_field] = training_items

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def get_chinese_questions_without_training(
    data_dir: str,
    skip_if_exists: bool = True,
    output_field: str = "chinese_modern_text_training",
) -> list[str]:
    questions = []

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(data_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tags = data.get("tags", [])
        if "语文" not in tags:
            continue

        if skip_if_exists and output_field in data:
            continue

        questions.append(filename.replace(".json", ""))

    return questions


def batch_process_chinese_modern_text(
    data_dir: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
    max_workers: int = 20,
    skip_if_exists: bool = True,
    output_field: str = "chinese_modern_text_training",
) -> dict:
    questions = get_chinese_questions_without_training(data_dir, skip_if_exists, output_field)

    def _process_one(qid):
        result = {"id": qid, "success": False, "message": ""}
        try:
            process_result = process_chinese_modern_text_question(
                data_dir=data_dir,
                question_id=qid,
                ai=ai,
                api_key=api_key,
                model=model,
                reasoning_effort=reasoning_effort,
                max_output_tokens=max_output_tokens,
                skip_if_exists=True,
                output_field=output_field,
            )
            if process_result.success:
                if process_result.error == "已存在处理结果":
                    result["message"] = "已存在"
                else:
                    result["success"] = True
                    result["message"] = f"生成了 {len(process_result.training_items)} 个训练项"
            else:
                result["message"] = process_result.error or "处理失败"
        except Exception as e:
            result["message"] = str(e)[:100]
        return result

    progress = run_batch(_process_one, questions, max_workers=max_workers, desc="语文现代文训练生成")

    return {
        "total": progress.total,
        "success": progress.success,
        "failed": progress.failed,
        "skipped": progress.skipped,
    }
