import os
import json
import threading
from typing import Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.base import AI, ReasoningEffort, call_ai, build_input_content, parse_items_text, extract_image_paths_from_items
from ai.thinking_processor import search_questions
from ai.immersion_thinking_prompt import get_immersion_thinking_prompt

print_lock = threading.Lock()


__all__ = [
    "ImmersionThinkingProcess",
    "generate_immersion_thinking",
    "generate_immersion_for_question",
    "batch_process_immersion_with_search",
]


@dataclass
class ImmersionThinkingProcess:
    thinking_content: str
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "thinking_content": self.thinking_content,
        }


def generate_immersion_thinking(
    question_text: str,
    answer_text: str,
    existing_thinking_content: str,
    image_paths: list[str],
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
) -> ImmersionThinkingProcess:
    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    prompt_text = f"""请对以下题目进行沉浸式思考过程深化，基于已有的思考内容进行扩展和深化：

原题：{question_text}

答案：{answer_text}

已有思考过程内容：
{existing_thinking_content}

请严格按照系统提示词中的格式要求，基于以上思考过程，输出更深入、更全面的沉浸式思考过程。"""

    user_content = build_input_content(prompt_text, image_paths)
    raw_response = call_ai(final_ai, get_immersion_thinking_prompt(), user_content)

    return ImmersionThinkingProcess(
        thinking_content=raw_response,
        raw_response=raw_response
    )


def generate_immersion_for_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    data: Optional[dict] = None
) -> Optional[ImmersionThinkingProcess]:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return None

    if data is None:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    existing_processes = data.get("thinking_processes", [])
    if not existing_processes:
        return None

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)

    image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

    existing_content = "\n\n".join([
        p.get("thinking_content", "") for p in existing_processes if p.get("thinking_content")
    ])

    return generate_immersion_thinking(
        question_text=question_text,
        answer_text=answer_text,
        existing_thinking_content=existing_content,
        image_paths=image_paths,
        ai=ai,
        api_key=api_key,
        model=model,
    )


def save_immersion_to_json(
    data_dir: str,
    question_id: str,
    immersion: ImmersionThinkingProcess
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "immersion_thinking_processes" not in data:
        data["immersion_thinking_processes"] = []

    data["immersion_thinking_processes"].append(immersion.to_dict())

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def batch_process_immersion_with_search(
    data_dir: str,
    search_query: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 3,
) -> dict:
    matched_ids = search_questions(data_dir, search_query)

    results = {
        "total": len(matched_ids),
        "success": [],
        "failed": [],
        "skipped": []
    }

    total = len(matched_ids)
    print(f"发现 {total} 个题目需要处理")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    def _process_one(qid: str, index: int) -> dict:
        result = {"id": qid, "success": False, "message": ""}

        try:
            immersion = generate_immersion_for_question(
                data_dir=data_dir,
                question_id=qid,
                ai=ai,
                api_key=api_key,
                model=model,
            )

            if immersion is None:
                result["message"] = "无现有思考过程"
            else:
                save_immersion_to_json(data_dir, qid, immersion)
                result["success"] = True
                result["message"] = "处理完成"

        except Exception as e:
            result["message"] = str(e)[:100]

        with print_lock:
            status = "✓" if result["success"] else "✗"
            print(f"[{index}/{total}] {status} {qid}: {result['message'][:50]}")

        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_one, qid, i): qid
            for i, qid in enumerate(matched_ids, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif result["message"] == "无现有思考过程":
                results["skipped"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, 跳过 {len(results['skipped'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason']}")

    return results
