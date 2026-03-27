import os
import re
import json
import base64
import threading
from typing import Optional, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from volcenginesdkarkruntime import Ark

from ai.thinking_process_prompt import get_thinking_process_prompt

print_lock = threading.Lock()

__all__ = [
    "ThinkingProcess",
    "ThinkingTarget",
    "encode_image_to_base64",
    "get_image_media_type",
    "generate_thinking_process",
    "generate_thinking_process_for_targets",
    "save_thinking_process_to_json",
    "search_questions",
    "batch_process_with_search",
]


@dataclass
class ThinkingTarget:
    target_id: str
    target_label: str
    question_text: str
    answer_text: str
    image_paths: list[str]


@dataclass
class ThinkingProcess:
    target_id: str
    target_label: str
    thinking_content: str
    raw_response: str

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_label": self.target_label,
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


def get_effective_tags(data: dict) -> list[str]:
    own_tags = data.get("tags", [])
    sub_question_tags = []
    for sq in data.get("sub_questions", []):
        sub_question_tags.extend(sq.get("tags", []))
    return list(set(own_tags + sub_question_tags))


def match_tag(tag_pattern: str, question_tags: list[str]) -> bool:
    tag_pattern_lower = tag_pattern.lower()
    for qt in question_tags:
        if tag_pattern_lower == qt.lower():
            return True
    return False


def match_text(text_pattern: str, question_str: str, answer_str: str) -> bool:
    pattern_lower = text_pattern.lower()
    return pattern_lower in question_str.lower() or pattern_lower in answer_str.lower()


def tokenize_search_query(query: str) -> list:
    tokens = []
    i = 0
    while i < len(query):
        if query[i] == '(':
            tokens.append(('LPAREN', '('))
            i += 1
        elif query[i] == ')':
            tokens.append(('RPAREN', ')'))
            i += 1
        elif query[i:i+3].upper() == 'AND' and (i + 3 >= len(query) or not query[i+3].isalnum()):
            tokens.append(('AND', 'AND'))
            i += 3
        elif query[i] == '|':
            tokens.append(('OR', '|'))
            i += 1
        elif query[i:i+2].upper() == 'OR' and (i + 2 >= len(query) or not query[i+2].isalnum()):
            tokens.append(('OR', 'OR'))
            i += 2
        elif query[i] == '-' and (not tokens or tokens[-1][0] in ('AND', 'OR', 'LPAREN', 'NOT', 'TEXT')):
            tokens.append(('NOT', '-'))
            i += 1
        elif query[i:i+3].upper() == 'NOT' and (i + 3 >= len(query) or not query[i+3].isalnum()):
            tokens.append(('NOT', 'NOT'))
            i += 3
        elif query[i] == ' ':
            i += 1
        elif query[i:i+4].upper() == 'TAG:':
            tag_name = query[i+4:]
            end = i + 4
            while end < len(query) and query[end] not in ' ()|-':
                end += 1
            tokens.append(('TAG', query[i+4:end]))
            i = end
        else:
            match = re.match(r'([^\s()\-:|]+)', query[i:])
            if match:
                tokens.append(('TEXT', match.group(1)))
                i += len(match.group(1))
            else:
                i += 1
    return tokens


def parse_and_evaluate(tokens: list, pos: int):
    result, pos = parse_or(tokens, pos)
    return result, pos


def parse_or(tokens: list, pos: int):
    left, pos = parse_and(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == 'OR':
        pos += 1
        right, pos = parse_and(tokens, pos)
        left = left | right
    return left, pos


def parse_and(tokens: list, pos: int):
    left, pos = parse_not(tokens, pos)
    while pos < len(tokens):
        token_type = tokens[pos][0]
        if token_type in ('AND', 'TAG', 'LPAREN'):
            if token_type == 'AND':
                pos += 1
            right, pos = parse_not(tokens, pos)
            left = left & right
        elif token_type == 'NOT':
            pos += 1
            right, pos = parse_atom(tokens, pos)
            left = left - right
        else:
            break
    return left, pos


def parse_not(tokens: list, pos: int):
    if pos < len(tokens) and tokens[pos][0] == 'NOT':
        pos += 1
        result, pos = parse_atom(tokens, pos)
        return set(range(100000)) - result, pos
    return parse_atom(tokens, pos)


def parse_atom(tokens: list, pos: int):
    if pos < len(tokens):
        token_type, token_val = tokens[pos]
        if token_type == 'TAG':
            return {'tag': token_val}, pos + 1
        elif token_type == 'TEXT':
            return {'text': token_val}, pos + 1
        elif token_type == 'LPAREN':
            pos += 1
            result, pos = parse_or(tokens, pos)
            if pos < len(tokens) and tokens[pos][0] == 'RPAREN':
                pos += 1
            return result, pos
    return set(), pos


def evaluate_ast(node, question_str: str, answer_str: str, tags: list[str]):
    if 'tag' in node:
        return match_tag(node['tag'], tags)
    elif 'text' in node:
        return match_text(node['text'], question_str, answer_str)
    elif 'and' in node:
        return all(evaluate_ast(child, question_str, answer_str, tags) for child in node['and'])
    elif 'or' in node:
        return any(evaluate_ast(child, question_str, answer_str, tags) for child in node['or'])
    elif 'not' in node:
        return not evaluate_ast(node['not'], question_str, answer_str, tags)
    return True


def search_questions(data_dir: str, query: str) -> list[str]:
    if not query.strip():
        question_ids = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                question_ids.append(filename[:-5])
        return question_ids

    tokens = tokenize_search_query(query)

    all_question_ids = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            all_question_ids.append(filename[:-5])

    matching_ids = []

    for qid in all_question_ids:
        filepath = os.path.join(data_dir, f"{qid}.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        question_str = json.dumps(data.get('question', {}), ensure_ascii=False)
        answer_str = json.dumps(data.get('answer', {}), ensure_ascii=False)
        tags = get_effective_tags(data)

        matched = True
        i = 0
        while i < len(tokens):
            token_type, token_val = tokens[i]
            if token_type == 'TAG':
                if not match_tag(token_val, tags):
                    matched = False
                    break
            elif token_type == 'TEXT':
                if not match_text(token_val, question_str, answer_str):
                    matched = False
                    break
            elif token_type == 'AND':
                pass
            elif token_type == 'OR':
                pass
            elif token_type == 'NOT':
                pass
            elif token_type == 'LPAREN':
                pass
            elif token_type == 'RPAREN':
                pass
            i += 1

        if matched:
            matching_ids.append(qid)

    return matching_ids


def build_thinking_prompt(
    question_text: str,
    answer_text: str,
    target_label: str = "整个题目"
) -> str:
    if target_label == "整个题目":
        prompt = f"""请对以下题目进行全维度思考过程还原：

原题：{question_text}

答案：{answer_text}

请严格按照系统提示词中的格式要求，输出完整的思考过程。"""
    else:
        prompt = f"""请对以下题目的部分内容进行全维度思考过程还原：

原题：{question_text}

答案：{answer_text}

需要生成思考过程的部分：{target_label}

请严格按照系统提示词中的格式要求，输出完整的思考过程。"""
    return prompt


def generate_thinking_process(
    question_text: str,
    answer_text: str,
    image_paths: list[str],
    target_label: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
    max_output_tokens: int = 131072,
    reasoning_effort: str = "high",
) -> ThinkingProcess:
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

    prompt_text = build_thinking_prompt(question_text, answer_text, target_label)

    input_content.append({
        "type": "input_text",
        "text": prompt_text
    })

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": get_thinking_process_prompt()}]
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

    return ThinkingProcess(
        target_id="",
        target_label=target_label,
        thinking_content=raw_response,
        raw_response=raw_response
    )


def extract_thinking_targets(
    data_dir: str,
    question_id: str,
    data: Optional[dict] = None
) -> list[ThinkingTarget]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    if data is None:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    tags = get_effective_tags(data)

    if "思维" not in tags:
        return []

    base_path = os.path.dirname(os.path.dirname(file_path))

    def parse_text(items):
        text_parts = []
        for item in items:
            if item.get("type") in ("text", "richtext"):
                text_parts.append(item.get("content", ""))
        return "".join(text_parts)

    question_items = data.get("question", {}).get("items", [])
    answer_items = data.get("answer", {}).get("items", [])

    question_text = parse_text(question_items)
    answer_text = parse_text(answer_items)

    image_paths = []
    for item in question_items + answer_items:
        if item.get("type") == "image":
            src = item.get("src", "")
            if src:
                full_path = os.path.normpath(os.path.join(base_path, src))
                image_paths.append(full_path)

    sub_questions = data.get("sub_questions", [])

    targets = []

    has_subquestion_with_tag = any(
        "思维" in subq.get("tags", [])
        for subq in sub_questions
    )

    if sub_questions and has_subquestion_with_tag:
        for subq in sub_questions:
            if "思维" in subq.get("tags", []):
                subq_text_items = subq.get("question_text", {}).get("items", [])
                subq_text = parse_text(subq_text_items)

                subq_images = []
                for item in subq_text_items:
                    if item.get("type") == "image":
                        src = item.get("src", "")
                        if src:
                            full_path = os.path.normpath(os.path.join(base_path, src))
                            subq_images.append(full_path)

                targets.append(ThinkingTarget(
                    target_id=str(subq.get("id", "")),
                    target_label=subq.get("title", "小问"),
                    question_text=subq_text,
                    answer_text=answer_text,
                    image_paths=subq_images
                ))
    else:
        targets.append(ThinkingTarget(
            target_id="full",
            target_label="整个题目",
            question_text=question_text,
            answer_text=answer_text,
            image_paths=image_paths
        ))

    return targets


def generate_thinking_process_for_targets(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> list[ThinkingProcess]:
    targets = extract_thinking_targets(data_dir, question_id)

    if not targets:
        return []

    results = []
    for target in targets:
        process = generate_thinking_process(
            question_text=target.question_text,
            answer_text=target.answer_text,
            image_paths=target.image_paths,
            target_label=target.target_label,
            api_key=api_key,
            model=model
        )
        process.target_id = target.target_id
        results.append(process)

    return results


def save_thinking_process_to_json(
    data_dir: str,
    question_id: str,
    processes: list[ThinkingProcess]
) -> bool:
    if not processes:
        return False

    file_path = os.path.join(data_dir, f"{question_id}.json")

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "thinking_processes" not in data:
        data["thinking_processes"] = []

    for process in processes:
        data["thinking_processes"].append(process.to_dict())

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def process_question_with_thinking_tag(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> list[ThinkingProcess]:
    processes = generate_thinking_process_for_targets(
        data_dir, question_id, api_key, model
    )

    if processes:
        save_thinking_process_to_json(data_dir, question_id, processes)

    return processes


def process_single_thinking(
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

        existing_processes = data.get("thinking_processes", [])
        if existing_processes:
            result["message"] = "already_exists"
            return result

        targets = extract_thinking_targets(data_dir, qid, data)

        if not targets:
            result["message"] = "no_thinking_tag"
            return result

        processes = generate_thinking_process_for_targets(
            data_dir, qid, api_key, model
        )

        if processes:
            save_thinking_process_to_json(data_dir, qid, processes)
            result["success"] = True
            result["message"] = "success"
        else:
            result["message"] = "no_targets"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        msg_display = result["message"] if not result["success"] else ""
        print(f"[{index}/{total}] {status} {qid}: {msg_display}")

    return result


def batch_process_with_search(
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
        "skipped_no_thinking_tag": [],
        "skipped_already_exists": []
    }

    total = len(matched_ids)
    print(f"发现 {total} 个题目需要生成思维过程")
    print(f"并发数: {max_workers}")
    print("=" * 60)

    if total == 0:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_thinking, data_dir, qid, api_key, model, i, total): qid
            for i, qid in enumerate(matched_ids, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif result["message"] == "already_exists":
                results["skipped_already_exists"].append(result["id"])
            elif result["message"] == "no_thinking_tag":
                results["skipped_no_thinking_tag"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, "
          f"跳过(已存在) {len(results['skipped_already_exists'])} 个, "
          f"跳过(无思维标签) {len(results['skipped_no_thinking_tag'])} 个")

    if results["failed"]:
        print("\n失败列表:")
        for item in results["failed"]:
            print(f"  - {item['id']}: {item['reason']}")

    return results
