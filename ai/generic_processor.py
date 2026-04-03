import os
import json
import threading
import requests
from typing import Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

from ai.base import (
    AI,
    ReasoningEffort,
    call_ai,
    build_input_content,
    parse_items_text,
    extract_image_paths_from_items,
)

print_lock = threading.Lock()

DEFAULT_API_BASE_URL = "http://localhost:5000"

__all__ = [
    "GenericAIResult",
    "GenericTarget",
    "search_questions_via_api",
    "get_question_via_api",
    "process_with_generic_ai",
    "batch_process_generic",
    "batch_process_generic_by_ids",
]


@dataclass
class GenericTarget:
    target_id: str
    target_label: str
    question_text: str
    answer_text: str
    image_paths: list[str]


@dataclass
class GenericAIResult:
    target_id: str
    target_label: str
    content: str
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_label": self.target_label,
            "content": self.content,
        }


def search_questions_via_api(
    search_query: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
    page_size: int = 1000,
) -> list[str]:
    all_ids = []
    page = 1

    while True:
        params = {
            "page": page,
            "page_size": page_size,
            "search": search_query
        }

        url = f"{api_base_url}/api/questions?{urlencode(params)}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            questions = data.get("questions", [])
            for q in questions:
                qid = q.get("id")
                if qid:
                    all_ids.append(qid)

            total_pages = data.get("total_pages", 1)

            if page >= total_pages:
                break

            page += 1

        except requests.RequestException as e:
            print(f"API 请求失败: {e}")
            break

    return all_ids


def get_question_via_api(
    question_id: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> Optional[dict]:
    params = {
        "page": 1,
        "page_size": 1,
        "search": question_id
    }

    url = f"{api_base_url}/api/questions?{urlencode(params)}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        questions = data.get("questions", [])
        if questions:
            return questions[0]

    except requests.RequestException as e:
        print(f"API 请求失败: {e}")

    return None


def extract_generic_targets(
    data_dir: str,
    question_id: str,
    data: Optional[dict] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
) -> list[GenericTarget]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if data is None:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_items_text(question_items)
    answer_text = parse_items_text(answer_items)

    image_paths = extract_image_paths_from_items(question_items + answer_items, data_dir)

    sub_questions = data.get("sub_questions", [])

    targets = []

    if not enable_sub_question_filter:
        targets.append(GenericTarget(
            target_id="full",
            target_label="整个题目",
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths
        ))
        return targets

    if not sub_questions:
        targets.append(GenericTarget(
            target_id="full",
            target_label="整个题目",
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths
        ))
        return targets

    for subq in sub_questions:
        subq_tags = subq.get("tags", [])

        if sub_question_tags:
            if require_all_sub_tags:
                if not all(tag in subq_tags for tag in sub_question_tags):
                    continue
            else:
                if not any(tag in subq_tags for tag in sub_question_tags):
                    continue

        subq_text_items = subq.get("question_text", {}).get("items", [])
        subq_text = parse_items_text(subq_text_items)

        subq_images = extract_image_paths_from_items(subq_text_items, data_dir)

        targets.append(GenericTarget(
            target_id=str(subq.get("id", "")),
            target_label=subq.get("title", "小问"),
            question_text=subq_text,
            answer_text=answer_text,
            image_paths=subq_images if subq_images else image_paths
        ))

    if not targets:
        targets.append(GenericTarget(
            target_id="full",
            target_label="整个题目",
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths
        ))

    return targets


def build_user_prompt(
    question_text: str,
    answer_text: str,
    target_label: str,
    extra_context: Optional[str] = None,
) -> str:
    prompt = f"""请对以下题目进行处理：

【题目】
{question_text}

【答案】
{answer_text if answer_text else "暂无答案"}"""

    if target_label != "整个题目":
        prompt += f"""

【需处理小问】
{target_label}"""

    if extra_context:
        prompt += f"""

【额外上下文】
{extra_context}"""

    return prompt


def call_ai_for_target(
    ai: AI,
    system_prompt: str,
    target: GenericTarget,
    extra_context: Optional[str] = None,
) -> str:
    prompt_text = build_user_prompt(
        target.question_text,
        target.answer_text,
        target.target_label,
        extra_context
    )
    user_content = build_input_content(prompt_text, target.image_paths)
    return call_ai(ai, system_prompt, user_content)


def process_single_target(
    target: GenericTarget,
    system_prompt: str,
    ai: Optional[AI] = None,
    extra_context: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_output_tokens: Optional[int] = None,
) -> GenericAIResult:
    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )
    
    raw_response = call_ai_for_target(final_ai, system_prompt, target, extra_context)

    return GenericAIResult(
        target_id=target.target_id,
        target_label=target.target_label,
        content=raw_response,
        raw_response=raw_response
    )


def process_with_generic_ai(
    data_dir: str,
    question_id: str,
    system_prompt: str,
    output_field: str = "generic_ai_result",
    ai: Optional[AI] = None,
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
) -> list[GenericAIResult]:
    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if skip_if_exists and output_field in data:
        existing = data.get(output_field, [])
        if existing:
            return []

    targets = extract_generic_targets(
        data_dir,
        question_id,
        data,
        sub_question_tags,
        require_all_sub_tags,
        enable_sub_question_filter,
    )

    if not targets:
        return []

    base_ai = ai or AI()
    final_ai = base_ai.with_overrides(
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        api_key=api_key,
    )

    results = []
    for target in targets:
        result = process_single_target(
            target=target,
            system_prompt=system_prompt,
            ai=final_ai,
            extra_context=extra_context,
        )
        results.append(result)

    if results:
        save_generic_results(data_dir, question_id, results, output_field)

    return results


def save_generic_results(
    data_dir: str,
    question_id: str,
    results: list[GenericAIResult],
    output_field: str,
) -> bool:
    if not results:
        return False

    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data[output_field] = [r.to_dict() for r in results]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_single_question_generic(
    data_dir: str,
    qid: str,
    system_prompt: str,
    output_field: str,
    ai: Optional[AI],
    extra_context: Optional[str],
    sub_question_tags: Optional[list[str]],
    require_all_sub_tags: bool,
    enable_sub_question_filter: bool,
    skip_if_exists: bool,
    api_key: Optional[str],
    model: Optional[str],
    max_output_tokens: Optional[int],
    reasoning_effort: Optional[Union[ReasoningEffort, str]],
    index: int,
    total: int
) -> dict:
    result = {"id": qid, "success": False, "message": ""}

    try:
        results = process_with_generic_ai(
            data_dir=data_dir,
            question_id=qid,
            system_prompt=system_prompt,
            output_field=output_field,
            ai=ai,
            extra_context=extra_context,
            sub_question_tags=sub_question_tags,
            require_all_sub_tags=require_all_sub_tags,
            enable_sub_question_filter=enable_sub_question_filter,
            skip_if_exists=skip_if_exists,
            api_key=api_key,
            model=model,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )

        if results:
            result["success"] = True
            result["message"] = f"处理了 {len(results)} 个目标"
        else:
            result["message"] = "无目标或已存在"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {qid}: {result['message'][:50]}")

    return result


def batch_process_generic_by_ids(
    data_dir: str,
    question_ids: list[str],
    system_prompt: str,
    output_field: str = "generic_ai_result",
    ai: Optional[AI] = None,
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_workers: int = 3,
) -> dict:
    results = {
        "total": len(question_ids),
        "success": [],
        "failed": [],
        "skipped": []
    }

    total = len(question_ids)
    print(f"共 {total} 个题目需要处理")
    print(f"输出字段: {output_field}")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_single_question_generic,
                data_dir, qid, system_prompt, output_field,
                ai, extra_context, sub_question_tags, require_all_sub_tags,
                enable_sub_question_filter, skip_if_exists,
                api_key, model, max_output_tokens, reasoning_effort, i, total
            ): qid
            for i, qid in enumerate(question_ids, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif result["message"] == "无目标或已存在":
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


def batch_process_generic(
    data_dir: str,
    system_prompt: str,
    search_query: str = "",
    output_field: str = "generic_ai_result",
    ai: Optional[AI] = None,
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    max_workers: int = 3,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> dict:
    matched_ids = search_questions_via_api(search_query, api_base_url)

    results = {
        "total_searched": len(matched_ids),
        "success": [],
        "failed": [],
        "skipped": []
    }

    total = len(matched_ids)
    print(f"发现 {total} 个题目需要处理")
    print(f"输出字段: {output_field}")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_single_question_generic,
                data_dir, qid, system_prompt, output_field,
                ai, extra_context, sub_question_tags, require_all_sub_tags,
                enable_sub_question_filter, skip_if_exists,
                api_key, model, max_output_tokens, reasoning_effort, i, total
            ): qid
            for i, qid in enumerate(matched_ids, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif result["message"] == "无目标或已存在":
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
