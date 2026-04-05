import os
import json
import threading
from typing import Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.base import AI, ReasoningEffort, call_ai, build_input_content
from ai.loader import ProcessedQuestion, load_question_by_id
from ai.advanced import parse_json_result

print_lock = threading.Lock()

__all__ = [
    "ChemistryPreprocessing",
    "get_chemistry_prompt",
    "generate_chemistry_preprocessing",
    "generate_chemistry_preprocessing_by_id",
    "save_chemistry_preprocessing_to_json",
    "process_chemistry_question",
    "batch_process_chemistry",
]

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "tsc", "化学题目预处理.txt")


@dataclass
class ChemistryPreprocessing:
    Accumulation: list
    Difficulties: list
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "Accumulation": self.Accumulation,
            "Difficulties": self.Difficulties
        }


def get_chemistry_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def generate_chemistry_preprocessing(
    question: ProcessedQuestion,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
) -> ChemistryPreprocessing:
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

    prompt_text = f"""请对以下化学题目进行预处理分析：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""

    user_content = build_input_content(prompt_text, question.image_paths)
    raw_response = call_ai(final_ai, get_chemistry_prompt(), user_content)

    try:
        result = parse_json_result(raw_response)
    except ValueError as e:
        raise ValueError(f"AI返回内容不是有效的JSON格式:\n{raw_response[:500]}") from e

    return ChemistryPreprocessing(
        Accumulation=result.get("Accumulation", []),
        Difficulties=result.get("Difficulties", []),
        raw_response=raw_response
    )


def generate_chemistry_preprocessing_by_id(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[ChemistryPreprocessing]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_chemistry_preprocessing(question, ai=ai, api_key=api_key, model=model)


def save_chemistry_preprocessing_to_json(
    data_dir: str,
    question_id: str,
    preprocessing: ChemistryPreprocessing
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["chemistry_preprocessing"] = preprocessing.to_dict()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_chemistry_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    skip_if_exists: bool = True,
) -> Optional[ChemistryPreprocessing]:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if skip_if_exists and "chemistry_preprocessing" in data:
        return None

    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None

    result = generate_chemistry_preprocessing(question, ai=ai, api_key=api_key, model=model)

    save_chemistry_preprocessing_to_json(data_dir, question_id, result)

    return result


def get_chemistry_questions_without_preprocessing(
    data_dir: str,
    skip_if_exists: bool = True
) -> list[str]:
    questions = []

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(data_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tags = data.get("tags", [])
        if "化学" not in tags:
            continue

        if skip_if_exists and "chemistry_preprocessing" in data:
            continue

        questions.append(filename.replace(".json", ""))

    return questions


def _process_single_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI],
    api_key: Optional[str],
    model: Optional[str],
    index: int,
    total: int
) -> dict:
    result = {"id": question_id, "success": False, "message": ""}

    try:
        preprocessing = process_chemistry_question(
            data_dir=data_dir,
            question_id=question_id,
            ai=ai,
            api_key=api_key,
            model=model,
            skip_if_exists=True,
        )

        if preprocessing:
            result["success"] = True
            result["message"] = f"Accumulation: {len(preprocessing.Accumulation)}条, Difficulties: {len(preprocessing.Difficulties)}条"
        else:
            result["message"] = "已存在或题目不存在"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {question_id}: {result['message'][:50]}")

    return result


def batch_process_chemistry(
    data_dir: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 3,
    skip_if_exists: bool = True,
) -> dict:
    questions = get_chemistry_questions_without_preprocessing(data_dir, skip_if_exists)
    total = len(questions)

    results = {
        "total": total,
        "success": [],
        "failed": [],
        "skipped": []
    }

    print(f"发现 {total} 个化学题目需要预处理")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _process_single_question,
                data_dir, qid, ai, api_key, model, i, total
            ): qid
            for i, qid in enumerate(questions, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif "已存在" in result["message"]:
                results["skipped"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason']}")

    return results
