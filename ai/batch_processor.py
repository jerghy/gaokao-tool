import json
import os
import threading
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ai.neural_reaction import preprocess_and_save

print_lock = threading.Lock()

__all__ = [
    "get_questions_without_reaction",
    "process_single_question",
    "batch_process",
]


def get_questions_without_reaction(
    data_dir: str,
    tags: Optional[list[str]] = None,
    require_all_tags: bool = False
) -> list[str]:
    questions = []

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(data_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "neural_reaction" in data:
            continue

        if tags:
            question_tags = data.get("tags", [])
            if require_all_tags:
                if not all(tag in question_tags for tag in tags):
                    continue
            else:
                if not any(tag in question_tags for tag in tags):
                    continue

        question_id = filename.replace(".json", "")
        questions.append(question_id)

    return questions


def process_single_question(
    data_dir: str,
    question_id: str,
    index: int,
    total: int
) -> dict:
    result = {"id": question_id, "success": False, "message": ""}

    try:
        reaction = preprocess_and_save(data_dir, question_id)

        if reaction:
            result["success"] = True
            result["message"] = reaction.core_conclusion[:50] + "..."
        else:
            result["message"] = "题目不存在"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {question_id}: {result['message'][:50]}")

    return result


def batch_process(
    data_dir: str,
    tags: Optional[list[str]] = None,
    require_all_tags: bool = False,
    max_workers: int = 5
) -> dict:
    questions = get_questions_without_reaction(data_dir, tags, require_all_tags)
    total = len(questions)

    results = {
        "total": total,
        "success": [],
        "failed": []
    }

    tag_info = ""
    if tags:
        tag_join = " 且 ".join(tags) if require_all_tags else " 或 ".join(tags)
        tag_info = f" (标签筛选: {tag_join})"

    print(f"发现 {total} 个题目需要生成神经反应{tag_info}")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_question, data_dir, qid, i, total): qid
            for i, qid in enumerate(questions, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason'][:50]}")

    return results
