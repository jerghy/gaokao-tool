import os
import base64
import json
from typing import Optional
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark

from ai.loader import ProcessedQuestion, load_question_by_id
from ai.evaluation_prompt import get_evaluation_prompt


__all__ = [
    "QualityEvaluation",
    "encode_image_to_base64",
    "get_image_media_type",
    "evaluate_question_quality",
    "evaluate_question_by_id",
    "save_evaluation_to_json",
    "evaluate_and_save",
]


@dataclass
class QualityEvaluation:
    question_basic_info: dict
    quality_total_grade: str
    grade_judgment_basis: str
    dimension_scores: dict
    core_value_highlights: str
    core_defects_or_flaws: str
    suitable_practice_scene: str
    practice_usage_suggestion: str
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "question_basic_info": self.question_basic_info,
            "quality_total_grade": self.quality_total_grade,
            "grade_judgment_basis": self.grade_judgment_basis,
            "dimension_scores": self.dimension_scores,
            "core_value_highlights": self.core_value_highlights,
            "core_defects_or_flaws": self.core_defects_or_flaws,
            "suitable_practice_scene": self.suitable_practice_scene,
            "practice_usage_suggestion": self.practice_usage_suggestion
        }


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


def evaluate_question_quality(
    question: ProcessedQuestion,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> QualityEvaluation:
    if api_key is None:
        api_key = os.getenv("ARK_API_KEY")

    if not api_key:
        raise ValueError("API KEY未配置，请设置ARK_API_KEY环境变量或传入api_key参数")

    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
        timeout=1800,
    )

    input_content = []

    for image_path in question.image_paths:
        if os.path.exists(image_path):
            base64_image = encode_image_to_base64(image_path)
            media_type = get_image_media_type(image_path)
            input_content.append({
                "type": "input_image",
                "image_url": f"data:{media_type};base64,{base64_image}"
            })

    prompt_text = f"""请对以下题目进行质量评价：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出评价结果。"""

    input_content.append({
        "type": "input_text",
        "text": prompt_text
    })

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": get_evaluation_prompt()}]
            },
            {
                "role": "user",
                "content": input_content
            }
        ],
        max_output_tokens=max_output_tokens,
        reasoning={"effort": reasoning_effort},
    )

    raw_response = response.output_text

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
        raise ValueError(f"AI返回内容不是有效的JSON格式:\n{raw_response}")

    return QualityEvaluation(
        question_basic_info=result.get("question_basic_info", {}),
        quality_total_grade=result.get("quality_total_grade", ""),
        grade_judgment_basis=result.get("grade_judgment_basis", ""),
        dimension_scores=result.get("dimension_scores", {}),
        core_value_highlights=result.get("core_value_highlights", ""),
        core_defects_or_flaws=result.get("core_defects_or_flaws", ""),
        suitable_practice_scene=result.get("suitable_practice_scene", ""),
        practice_usage_suggestion=result.get("practice_usage_suggestion", ""),
        raw_response=raw_response
    )


def evaluate_question_by_id(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QualityEvaluation]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return evaluate_question_quality(question, api_key, model)


def save_evaluation_to_json(
    data_dir: str,
    question_id: str,
    evaluation: QualityEvaluation
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["quality_evaluation"] = evaluation.to_dict()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def evaluate_and_save(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QualityEvaluation]:
    evaluation = evaluate_question_by_id(data_dir, question_id, api_key, model)

    if evaluation is None:
        return None

    save_evaluation_to_json(data_dir, question_id, evaluation)

    return evaluation
