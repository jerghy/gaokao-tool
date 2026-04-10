import os
import json
import logging
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import (
    AI,
    ReasoningEffort,
    call_ai,
    call_ai_json,
    build_input_content,
    parse_items_text,
    extract_image_paths_from_items,
)
from ai.batch import run_batch

logger = logging.getLogger(__name__)

__all__ = [
    "MathUnit",
    "MathProcessResult",
    "load_math_prompt",
    "MATH_SPLIT_CLASSIFY_PROMPT",
    "MATH_THINKING_CHAIN_PROMPT",
    "MATH_AI_STAGE1",
    "MATH_AI_STAGE2",
    "split_and_classify",
    "deep_parse_thinking",
    "process_math_question",
    "batch_process_math_questions",
]

_TSC_DIR = os.path.join(os.path.dirname(__file__), "tsc")


def load_math_prompt(prompt_name: str) -> str:
    file_path = os.path.join(_TSC_DIR, f"{prompt_name}.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"提示词文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


MATH_SPLIT_CLASSIFY_PROMPT = load_math_prompt("Math_Topic_Split_Classify_Preprocess_Prompt")
MATH_THINKING_CHAIN_PROMPT = load_math_prompt("Math_Thinking_Chain_Deep_Parse_Prompt")

MATH_AI_STAGE1 = AI(
    model="doubao-seed-2-0-pro-260215",
    reasoning_effort=ReasoningEffort.high,
    max_output_tokens=131072,
)
MATH_AI_STAGE2 = AI(
    model="doubao-seed-2-0-pro-260215",
    reasoning_effort=ReasoningEffort.medium,
    max_output_tokens=131072,
)


@dataclass
class MathUnit:
    unit_content: str
    classify_result: str
    pre_process: Union[str, list]

    def to_dict(self) -> dict:
        return {
            "unit_content": self.unit_content,
            "classify_result": self.classify_result,
            "pre_process": self.pre_process,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MathUnit":
        return cls(
            unit_content=data.get("unit_content", ""),
            classify_result=data.get("classify_result", ""),
            pre_process=data.get("pre_process", ""),
        )


@dataclass
class MathProcessResult:
    question_id: str
    units: list[MathUnit]
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "units": [u.to_dict() for u in self.units],
            "success": self.success,
            "error": self.error,
        }


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


def split_and_classify(
    question_text: str,
    answer_text: str,
    image_paths: list[str],
    ai: Optional[AI] = None,
) -> list[MathUnit]:
    final_ai = ai or MATH_AI_STAGE1

    user_text = f"""【题目原文】
{question_text}

【标准答案】
{answer_text if answer_text else "暂无答案"}"""

    user_content = build_input_content(user_text, image_paths)

    result = call_ai_json(final_ai, MATH_SPLIT_CLASSIFY_PROMPT, user_content)

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            raise ValueError("AI输出格式不符合要求，非合规JSON数组")

    if not isinstance(result, list):
        raise ValueError("AI输出格式不符合要求，非合规JSON数组")

    units = []
    for item in result:
        if isinstance(item, dict):
            units.append(MathUnit.from_dict(item))

    return units


def deep_parse_thinking(
    question_text: str,
    answer_text: str,
    unit_content: str,
    pre_process: str,
    image_paths: list[str],
    ai: Optional[AI] = None,
) -> str:
    final_ai = ai or MATH_AI_STAGE2

    user_text = f"""【题目原文】
{question_text}

【标准答案】
{answer_text if answer_text else "暂无答案"}

【unit_content】
{unit_content}

【pre_process】
{pre_process}"""

    user_content = build_input_content(user_text, image_paths)

    result = call_ai(final_ai, MATH_THINKING_CHAIN_PROMPT, user_content)

    return result


def process_math_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    skip_if_exists: bool = True,
    output_field: str = "math_processing_result",
) -> MathProcessResult:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return MathProcessResult(
            question_id=question_id,
            units=[],
            success=False,
            error=f"题目文件不存在: {file_path}",
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if skip_if_exists and output_field in data:
        existing = data.get(output_field, [])
        if existing:
            return MathProcessResult(
                question_id=question_id,
                units=[],
                success=True,
                error="已存在处理结果",
            )

    try:
        data, question_text, answer_text, image_paths = _load_question_data(data_dir, question_id)

        units = split_and_classify(question_text, answer_text, image_paths, ai)

        final_units = []
        for unit in units:
            if unit.classify_result == "套路知识类":
                final_units.append(unit)
            elif unit.classify_result == "思维提升类":
                try:
                    pre_process_str = unit.pre_process if isinstance(unit.pre_process, str) else json.dumps(unit.pre_process, ensure_ascii=False)
                    deep_content = deep_parse_thinking(
                        question_text=question_text,
                        answer_text=answer_text,
                        unit_content=unit.unit_content,
                        pre_process=pre_process_str,
                        image_paths=image_paths,
                        ai=ai,
                    )
                    final_units.append(MathUnit(
                        unit_content=unit.unit_content,
                        classify_result=unit.classify_result,
                        pre_process=deep_content,
                    ))
                except Exception as e:
                    logger.warning(f"思维提升类深度处理失败: {e}")
                    final_units.append(unit)
            else:
                final_units.append(unit)

        _save_result(data_dir, question_id, final_units, output_field)

        return MathProcessResult(
            question_id=question_id,
            units=final_units,
            success=True,
        )

    except Exception as e:
        return MathProcessResult(
            question_id=question_id,
            units=[],
            success=False,
            error=str(e),
        )


def _save_result(
    data_dir: str,
    question_id: str,
    units: list[MathUnit],
    output_field: str,
) -> bool:
    if not units:
        return False

    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data[output_field] = [u.to_dict() for u in units]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def batch_process_math_questions(
    data_dir: str,
    question_ids: list[str],
    ai: Optional[AI] = None,
    skip_if_exists: bool = True,
    output_field: str = "math_processing_result",
    max_workers: int = 3,
) -> dict:
    def _process_one(qid):
        result = {"id": qid, "success": False, "message": ""}
        try:
            process_result = process_math_question(
                data_dir=data_dir, question_id=qid, ai=ai,
                skip_if_exists=skip_if_exists, output_field=output_field,
            )
            if process_result.success:
                if process_result.error == "已存在处理结果":
                    result["message"] = "已存在"
                else:
                    result["success"] = True
                    result["message"] = f"处理了 {len(process_result.units)} 个单元"
            else:
                result["message"] = process_result.error or "处理失败"
        except Exception as e:
            result["message"] = str(e)[:100]
        return result

    progress = run_batch(_process_one, question_ids, max_workers=max_workers, desc="数学处理")

    return {
        "total": progress.total,
        "success": progress.success,
        "failed": progress.failed,
        "skipped": progress.skipped,
    }
