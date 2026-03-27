import os
import base64
import json
import threading
import requests
from typing import Optional, List, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

from volcenginesdkarkruntime import Ark

print_lock = threading.Lock()

DEFAULT_API_BASE_URL = "http://localhost:5000"


def search_questions_via_api(
    search_query: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
    page_size: int = 1000,
) -> list[str]:
    """
    通过 HTTP API 搜索题目，返回匹配的题目 ID 列表
    
    Args:
        search_query: 搜索查询字符串，如 "tag:数学" 或 "(tag:生物 OR tag:化学) -tag:已掌握"
        api_base_url: API 基础地址
        page_size: 每页数量，默认足够大以获取所有结果
    
    Returns:
        list[str]: 匹配的题目 ID 列表
    """
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
            
            total = data.get("total", 0)
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
    """
    通过 HTTP API 获取单个题目数据
    
    Args:
        question_id: 题目 ID
        api_base_url: API 基础地址
    
    Returns:
        dict 或 None: 题目数据
    """
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

        subq_images = []
        for item in subq_text_items:
            if item.get("type") == "image":
                src = item.get("src", "")
                if src:
                    full_path = os.path.normpath(os.path.join(base_path, src))
                    subq_images.append(full_path)

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


def extract_response_text(response) -> str:
    """
    从 responses.create 返回的 Response 对象中提取输出文本
    """
    for item in response.output:
        if hasattr(item, 'content') and item.content:
            for c in item.content:
                if hasattr(c, 'text') and c.text:
                    return c.text
    return ""


def call_ai_api(
    system_prompt: str,
    question_text: str,
    answer_text: str,
    target_label: str,
    image_paths: list[str],
    extra_context: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> str:
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

    prompt_text = build_user_prompt(question_text, answer_text, target_label, extra_context)
    input_content.append({
        "type": "input_text",
        "text": prompt_text
    })

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}]
            },
            {
                "role": "user",
                "content": input_content
            }
        ],
        max_output_tokens=max_output_tokens,
        reasoning={"effort": reasoning_effort},
    )

    return extract_response_text(response)


def process_single_target(
    target: GenericTarget,
    system_prompt: str,
    extra_context: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> GenericAIResult:
    raw_response = call_ai_api(
        system_prompt=system_prompt,
        question_text=target.question_text,
        answer_text=target.answer_text,
        target_label=target.target_label,
        image_paths=target.image_paths,
        extra_context=extra_context,
        api_key=api_key,
        model=model,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )

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
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
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

    results = []
    for target in targets:
        result = process_single_target(
            target=target,
            system_prompt=system_prompt,
            extra_context=extra_context,
            api_key=api_key,
            model=model,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )
        results.append(result)

    if results:
        save_generic_results(data_dir, question_id, results, output_field)

    return results


def batch_process_generic_by_ids(
    data_dir: str,
    question_ids: list[str],
    system_prompt: str,
    output_field: str = "generic_ai_result",
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
    max_workers: int = 3,
) -> dict:
    """
    根据题目 ID 列表批量处理，支持多线程
    
    Args:
        data_dir: 数据目录
        question_ids: 题目 ID 列表
        system_prompt: AI 系统提示词
        output_field: JSON 保存字段名
        extra_context: 额外上下文
        sub_question_tags: 小问标签筛选
        require_all_sub_tags: 是否需要全部标签匹配
        enable_sub_question_filter: 是否开启小问筛选
        skip_if_exists: 已存在则跳过
        api_key: API 密钥
        model: 模型名称
        max_output_tokens: 最大输出 token 数
        reasoning_effort: 推理深度 (low/medium/high)
        max_workers: 并发数
    
    Returns:
        dict: 处理结果统计
    """
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
                extra_context, sub_question_tags, require_all_sub_tags,
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
    extra_context: Optional[str],
    sub_question_tags: Optional[list[str]],
    require_all_sub_tags: bool,
    enable_sub_question_filter: bool,
    skip_if_exists: bool,
    api_key: Optional[str],
    model: str,
    max_output_tokens: int,
    reasoning_effort: str,
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


def batch_process_generic(
    data_dir: str,
    system_prompt: str,
    search_query: str = "",
    output_field: str = "generic_ai_result",
    extra_context: Optional[str] = None,
    sub_question_tags: Optional[list[str]] = None,
    require_all_sub_tags: bool = False,
    enable_sub_question_filter: bool = False,
    skip_if_exists: bool = True,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
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
                extra_context, sub_question_tags, require_all_sub_tags,
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
