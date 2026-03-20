import json
import os
from typing import Optional
from dataclasses import dataclass


__all__ = [
    "ProcessedQuestion",
    "parse_items",
    "load_question_from_file",
    "load_question_by_id",
    "load_all_questions",
]


@dataclass
class ProcessedQuestion:
    question_text: str
    answer_text: str
    image_paths: list[str]


def parse_items(items: list[dict], base_path: str) -> tuple[str, list[str]]:
    """
    解析items列表，返回文本内容和图片路径列表

    Args:
        items: 题目或答案的items列表
        base_path: JSON文件所在目录，用于解析图片相对路径

    Returns:
        tuple: (文本内容, 图片路径列表)
    """
    text_parts = []
    image_paths = []

    for item in items:
        item_type = item.get("type", "")

        if item_type == "text":
            content = item.get("content", "")
            text_parts.append(content)

        elif item_type == "richtext":
            content = item.get("content", "")
            text_parts.append(content)

        elif item_type == "image":
            src = item.get("src", "")
            if src:
                image_name = os.path.basename(src)
                placeholder = f"[图片:{image_name}]"
                text_parts.append(placeholder)

                full_image_path = os.path.normpath(os.path.join(base_path, src))
                image_paths.append(full_image_path)

    return "".join(text_parts), image_paths


def load_question_from_file(file_path: str) -> ProcessedQuestion:
    """
    从JSON文件加载题目

    Args:
        file_path: JSON文件的完整路径

    Returns:
        ProcessedQuestion: 处理后的题目对象
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_path = os.path.dirname(os.path.dirname(file_path))

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text, question_images = parse_items(question_items, base_path)
    answer_text, answer_images = parse_items(answer_items, base_path)

    all_images = question_images + answer_images

    return ProcessedQuestion(
        question_text=question_text,
        answer_text=answer_text,
        image_paths=all_images
    )


def load_question_by_id(data_dir: str, question_id: str) -> Optional[ProcessedQuestion]:
    """
    根据题目ID加载题目

    Args:
        data_dir: 数据目录路径
        question_id: 题目ID（如"20260314002557"）

    Returns:
        ProcessedQuestion或None（如果文件不存在）
    """
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return None

    return load_question_from_file(file_path)


def load_all_questions(data_dir: str) -> list[ProcessedQuestion]:
    """
    加载目录中的所有题目

    Args:
        data_dir: 数据目录路径

    Returns:
        list[ProcessedQuestion]: 所有题目的列表
    """
    questions = []

    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(data_dir, filename)
            question = load_question_from_file(file_path)
            questions.append(question)

    return questions
