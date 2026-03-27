import os
import base64
import json
import threading
from typing import Optional, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from volcenginesdkarkruntime import Ark

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


def parse_items_text(items: list) -> str:
    text_parts = []
    for item in items:
        if item.get("type") in ("text", "richtext"):
            text_parts.append(item.get("content", ""))
    return "".join(text_parts)


def generate_immersion_thinking(
    question_text: str,
    answer_text: str,
    existing_thinking_content: str,
    image_paths: list[str],
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> ImmersionThinkingProcess:
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

    for image_path in image_paths:
        if os.path.exists(image_path):
            base64_image = encode_image_to_base64(image_path)
            media_type = get_image_media_type(image_path)
            input_content.append({
                "type": "input_image",
                "image_url": f"data:{media_type};base64,{base64_image}"
            })

    prompt_text = f"""请对以下题目进行沉浸式思考过程深化，基于已有的思考内容进行扩展和深化：

原题：{question_text}

答案：{answer_text}

已有思考过程内容：
{existing_thinking_content}

请严格按照系统提示词中的格式要求，基于以上思考过程，输出更深入、更全面的沉浸式思考过程。"""

    input_content.append({
        "type": "input_text",
        "text": prompt_text
    })

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": get_immersion_thinking_prompt()}]
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

    return ImmersionThinkingProcess(
        thinking_content=raw_response,
        raw_response=raw_response
    )


def generate_immersion_for_question(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
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

    base_path = os.path.dirname(os.path.dirname(file_path))

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)

    image_paths = []
    for item in question_items + answer_items:
        if item.get("type") == "image":
            src = item.get("src", "")
            if src:
                full_path = os.path.normpath(os.path.join(base_path, src))
                image_paths.append(full_path)

    existing_content = "\n\n".join([
        p.get("thinking_content", "")
        for p in existing_processes
        if p.get("thinking_content")
    ])

    return generate_immersion_thinking(
        question_text=question_text,
        answer_text=answer_text,
        existing_thinking_content=existing_content,
        image_paths=image_paths,
        api_key=api_key,
        model=model
    )


def save_immersion_to_json(
    data_dir: str,
    question_id: str,
    process: ImmersionThinkingProcess
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "immersion_thinking" not in data:
        data["immersion_thinking"] = []

    data["immersion_thinking"].append(process.to_dict())

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_single_immersion(
    data_dir: str,
    qid: str,
    api_key: Optional[str],
    model: str,
    index: int,
    total: int
) -> dict:
    result = {"id": qid, "success": False, "message": ""}

    try:
        file_path = os.path.join(data_dir, f"{qid}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_immersion = data.get("immersion_thinking", [])
        if existing_immersion:
            result["message"] = "already_exists"
            return result

        existing_processes = data.get("thinking_processes", [])
        if not existing_processes:
            result["message"] = "no_thinking"
            return result

        process = generate_immersion_for_question(
            data_dir, qid, api_key, model, data
        )

        if process:
            save_immersion_to_json(data_dir, qid, process)
            result["success"] = True
            result["message"] = "success"
        else:
            result["message"] = "no_process"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        msg_display = result["message"] if not result["success"] else ""
        print(f"[{index}/{total}] {status} {qid}: {msg_display}")

    return result


def batch_process_immersion_with_search(
    data_dir: str,
    search_query: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_workers: int = 3
) -> dict:
    matched_ids = search_questions(data_dir, search_query)

    results = {
        "total_searched": len(matched_ids),
        "success": [],
        "failed": [],
        "skipped_no_thinking": [],
        "skipped_already_exists": []
    }

    total = len(matched_ids)
    print(f"发现 {total} 个题目需要生成沉浸式思维")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_immersion, data_dir, qid, api_key, model, i, total): qid
            for i, qid in enumerate(matched_ids, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif result["message"] == "already_exists":
                results["skipped_already_exists"].append(result["id"])
            elif result["message"] == "no_thinking":
                results["skipped_no_thinking"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, "
          f"跳过(已存在) {len(results['skipped_already_exists'])} 个, "
          f"跳过(无思维) {len(results['skipped_no_thinking'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason']}")

    return results
