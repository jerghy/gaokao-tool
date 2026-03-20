import os
import base64
import json
from typing import Optional
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark

from ai.loader import ProcessedQuestion, load_question_by_id
from ai.neural_reaction_prompt import get_neural_reaction_prompt


__all__ = [
    "NeuralReaction",
    "encode_image_to_base64",
    "get_image_media_type",
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


def generate_neural_reaction(
    question: ProcessedQuestion,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> NeuralReaction:
    if api_key is None:
        api_key = os.getenv("ARK_API_KEY")

    if not api_key:
        raise ValueError("API KEY未配置，请设置ARK_API_KEY环境变量或传入api_key参数")

    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
        timeout=1800,
    )

    user_content = []

    for image_path in question.image_paths:
        if os.path.exists(image_path):
            base64_image = encode_image_to_base64(image_path)
            media_type = get_image_media_type(image_path)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{base64_image}"}
            })

    prompt_text = f"""请对以下题目生成神经刺激式积累反应：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""

    user_content.append({
        "type": "text",
        "text": prompt_text
    })

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": get_neural_reaction_prompt()
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        thinking={
            "type": "enabled",
        },
    )

    raw_response = response.choices[0].message.content

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
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[NeuralReaction]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_neural_reaction(question, api_key, model)


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
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[NeuralReaction]:
    reaction = generate_neural_reaction_by_id(data_dir, question_id, api_key, model)

    if reaction is None:
        return None

    save_neural_reaction_to_json(data_dir, question_id, reaction)

    return reaction
