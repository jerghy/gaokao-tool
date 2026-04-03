import os
import json
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import AI, ReasoningEffort, call_ai, build_input_content
from ai.loader import ProcessedQuestion, load_question_by_id
from ai.preprocessing_prompt_v2 import get_preprocessing_prompt_v2


__all__ = [
    "QuestionAnalysis",
    "generate_question_analysis",
    "generate_analysis_by_id",
    "save_analysis_to_json",
    "preprocess_and_save",
]


@dataclass
class QuestionAnalysis:
    question_basic_info: dict
    module_1_basic_model_analysis: dict
    module_2_student_trial_error_analysis: list
    module_3_multi_dimensional_solution_analysis: dict
    module_4_neural_stimulus_trigger_points: dict
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "question_basic_info": self.question_basic_info,
            "module_1_basic_model_analysis": self.module_1_basic_model_analysis,
            "module_2_student_trial_error_analysis": self.module_2_student_trial_error_analysis,
            "module_3_multi_dimensional_solution_analysis": self.module_3_multi_dimensional_solution_analysis,
            "module_4_neural_stimulus_trigger_points": self.module_4_neural_stimulus_trigger_points
        }


def generate_question_analysis(
    question: ProcessedQuestion,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
) -> QuestionAnalysis:
    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    prompt_text = f"""请对以下题目进行全维度预处理分析：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""

    user_content = build_input_content(prompt_text, question.image_paths)
    raw_response = call_ai(final_ai, get_preprocessing_prompt_v2(), user_content)

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

    return QuestionAnalysis(
        question_basic_info=result.get("question_basic_info", {}),
        module_1_basic_model_analysis=result.get("module_1_basic_model_analysis", {}),
        module_2_student_trial_error_analysis=result.get("module_2_student_trial_error_analysis", []),
        module_3_multi_dimensional_solution_analysis=result.get("module_3_multi_dimensional_solution_analysis", {}),
        module_4_neural_stimulus_trigger_points=result.get("module_4_neural_stimulus_trigger_points", {}),
        raw_response=raw_response
    )


def generate_analysis_by_id(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[QuestionAnalysis]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_question_analysis(question, ai=ai, api_key=api_key, model=model)


def save_analysis_to_json(
    data_dir: str,
    question_id: str,
    analysis: QuestionAnalysis
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["question_analysis"] = analysis.to_dict()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def preprocess_and_save(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[QuestionAnalysis]:
    analysis = generate_analysis_by_id(data_dir, question_id, ai=ai, api_key=api_key, model=model)

    if analysis is None:
        return None

    save_analysis_to_json(data_dir, question_id, analysis)

    return analysis
