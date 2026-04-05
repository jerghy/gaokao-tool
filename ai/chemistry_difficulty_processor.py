import os
import json
import threading
from typing import Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.base import AI, ReasoningEffort, call_ai, build_input_content
from ai.loader import ProcessedQuestion, load_question_by_id

print_lock = threading.Lock()

__all__ = [
    "DifficultyTeaching",
    "get_difficulty_prompt",
    "generate_difficulty_teaching",
    "process_difficulty_for_question",
    "get_questions_with_selected_difficulties",
    "batch_process_difficulties",
]

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "tsc", "化学难点.txt")


@dataclass
class DifficultyTeaching:
    difficulty_id: int
    content: str
    raw_response: str


def get_difficulty_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_difficulty_input(
    question_text: str,
    answer_text: str,
    difficulty_json: dict,
) -> str:
    return f"""## 输入1：高中化学原题完整内容

【题目】
{question_text}

【答案】
{answer_text if answer_text else "暂无答案"}

## 输入2：单个难点单元完整JSON内容

{json.dumps(difficulty_json, ensure_ascii=False, indent=2)}

请根据以上输入，按照系统提示词的要求生成完整的难点攻克教学内容。"""


def generate_difficulty_teaching(
    question: ProcessedQuestion,
    difficulty: dict,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
) -> DifficultyTeaching:
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

    prompt_text = build_difficulty_input(
        question.question_text,
        question.answer_text,
        difficulty,
    )

    user_content = build_input_content(prompt_text, question.image_paths)
    raw_response = call_ai(final_ai, get_difficulty_prompt(), user_content)

    return DifficultyTeaching(
        difficulty_id=difficulty.get("DifficultyID", 0),
        content=raw_response,
        raw_response=raw_response,
    )


def process_difficulty_for_question(
    data_dir: str,
    question_id: str,
    difficulty_id: int,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    skip_if_exists: bool = True,
) -> Optional[DifficultyTeaching]:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if skip_if_exists:
        existing = data.get("difficulty_teaching", {})
        if str(difficulty_id) in existing:
            return None

    preprocessing = data.get("chemistry_preprocessing", {})
    difficulties = preprocessing.get("Difficulties", [])

    target_difficulty = None
    for d in difficulties:
        if d.get("DifficultyID") == difficulty_id:
            target_difficulty = d
            break

    if not target_difficulty:
        return None

    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None

    result = generate_difficulty_teaching(question, target_difficulty, ai, api_key, model)

    if "difficulty_teaching" not in data:
        data["difficulty_teaching"] = {}
    data["difficulty_teaching"][str(difficulty_id)] = result.content

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return result


def get_questions_with_selected_difficulties(
    data_dir: str,
    skip_if_exists: bool = True
) -> list[dict]:
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

        preprocessing = data.get("chemistry_preprocessing", {})
        if not preprocessing:
            continue

        selected_ids = data.get("selected_difficulty_ids", [])
        if not selected_ids:
            continue

        existing_teaching = data.get("difficulty_teaching", {})
        pending_ids = [i for i in selected_ids if str(i) not in existing_teaching] if skip_if_exists else selected_ids

        if pending_ids:
            questions.append({
                "id": filename.replace(".json", ""),
                "pending_difficulty_ids": pending_ids,
            })

    return questions


def _process_single_task(
    data_dir: str,
    question_id: str,
    difficulty_id: int,
    ai: Optional[AI],
    api_key: Optional[str],
    model: Optional[str],
    index: int,
    total: int,
) -> dict:
    result = {
        "question_id": question_id,
        "difficulty_id": difficulty_id,
        "success": False,
        "message": "",
    }

    try:
        teaching = process_difficulty_for_question(
            data_dir=data_dir,
            question_id=question_id,
            difficulty_id=difficulty_id,
            ai=ai,
            api_key=api_key,
            model=model,
            skip_if_exists=True,
        )

        if teaching:
            result["success"] = True
            result["message"] = f"生成成功，内容长度: {len(teaching.content)} 字符"
        else:
            result["message"] = "已存在或难点不存在"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {question_id} - 难点{difficulty_id}: {result['message'][:30]}")

    return result


def batch_process_difficulties(
    data_dir: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 3,
    skip_if_exists: bool = True,
) -> dict:
    questions = get_questions_with_selected_difficulties(data_dir, skip_if_exists)

    tasks = []
    for q in questions:
        for diff_id in q["pending_difficulty_ids"]:
            tasks.append({
                "question_id": q["id"],
                "difficulty_id": diff_id,
            })

    total = len(tasks)
    results = {
        "total": total,
        "success": [],
        "failed": [],
        "skipped": [],
    }

    print(f"发现 {len(questions)} 个题目，共 {total} 个难点需要生成教学内容")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _process_single_task,
                data_dir, t["question_id"], t["difficulty_id"],
                ai, api_key, model, i, total
            ): t
            for i, t in enumerate(tasks, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result)
            elif "已存在" in result["message"]:
                results["skipped"].append(result)
            else:
                results["failed"].append(result)

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['question_id']} 难点{item['difficulty_id']}: {item['message']}")

    return results
