import os
import json
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import AI, ReasoningEffort, call_ai, build_input_content
from ai.loader import ProcessedQuestion, load_question_by_id
from ai.neural_reaction_prompt import get_neural_reaction_prompt


__all__ = [
    "NeuralReaction",
    "generate_neural_reaction",
    "generate_neural_reaction_by_id",
    "save_neural_reaction_to_json",
    "preprocess_and_save",
]


@dataclass
class NeuralReaction:
    core_conclusion: str
    reaction_dimensions: dict
    core_quick_memory_pack: list
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "core_conclusion": self.core_conclusion,
            "reaction_dimensions": self.reaction_dimensions,
            "core_quick_memory_pack": self.core_quick_memory_pack
        }


def generate_neural_reaction(
    question: ProcessedQuestion,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
) -> NeuralReaction:
    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    prompt_text = f"""请对以下题目生成神经刺激式积累反应：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""

    user_content = build_input_content(prompt_text, question.image_paths)
    raw_response = call_ai(final_ai, get_neural_reaction_prompt(), user_content)

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

    return NeuralReaction(
        core_conclusion=result.get("core_conclusion", ""),
        reaction_dimensions=result.get("reaction_dimensions", {}),
        core_quick_memory_pack=result.get("core_quick_memory_pack", []),
        raw_response=raw_response
    )


def generate_neural_reaction_by_id(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[NeuralReaction]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_neural_reaction(question, ai=ai, api_key=api_key, model=model)


def save_neural_reaction_to_json(
    data_dir: str,
    question_id: str,
    reaction: NeuralReaction
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["neural_reaction"] = reaction.to_dict()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def preprocess_and_save(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[NeuralReaction]:
    reaction = generate_neural_reaction_by_id(data_dir, question_id, ai=ai, api_key=api_key, model=model)

    if reaction is None:
        return None

    save_neural_reaction_to_json(data_dir, question_id, reaction)

    return reaction
