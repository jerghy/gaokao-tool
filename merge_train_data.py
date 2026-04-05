import os
import json
import argparse
import threading
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from volcenginesdkarkruntime import Ark

from ai.base import AI, call_ai_json, build_input_content, ReasoningEffort


def get_embedding(text: str) -> List[float]:
    client = Ark(
        api_key=os.getenv("ARK_API_KEY"),
        base_url="https://ark.cn-beijing.volces.com/api/v3"
    )
    
    response = client.multimodal_embeddings.create(
        model="doubao-embedding-vision-251215",
        input=[{"type": "text", "text": text}],
        encoding_format="float",
        dimensions=2048
    )
    
    return response.data.embedding


def get_text_for_embedding(item: Dict[str, Any], train_type: str) -> str:
    train_data = item.get("train_data", {})
    
    if train_type == "知识易错训练":
        content = train_data.get("train_content", "")
        answer = train_data.get("answer", "")
        return f"{content}\n{answer}"
    elif train_type == "套路反射训练":
        question = train_data.get("question", "")
        answer = train_data.get("standard_answer", "")
        return f"{question}\n{answer}"
    
    return ""


def vectorize_train_data(json_file: str, max_workers: int = 5, batch_save: int = 10) -> Dict[str, Any]:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_items = []
    for train_type in ["知识易错训练", "套路反射训练"]:
        for item in data.get(train_type, []):
            item["_train_type"] = train_type
            all_items.append(item)
    
    to_vectorize = []
    for i, item in enumerate(all_items):
        if "embedding" not in item:
            text = get_text_for_embedding(item, item.get("_train_type", ""))
            if text:
                to_vectorize.append((i, text))
    
    if not to_vectorize:
        print("所有数据已向量化，无需处理")
        return data
    
    total = len(to_vectorize)
    print(f"需要向量化的数据: {total} 条")
    
    print_lock = threading.Lock()
    completed = [0]
    batch_count = [0]
    
    def _vectorize_one(item):
        idx, text = item
        try:
            embedding = get_embedding(text)
            result = (idx, embedding, None)
        except Exception as e:
            result = (idx, None, str(e))
        
        with print_lock:
            completed[0] += 1
            batch_count[0] += 1
            print(f"\r向量化进度: {completed[0]}/{total}", end="", flush=True)
            
            if batch_count[0] >= batch_save:
                batch_count[0] = 0
                _save_batch(data, all_items, json_file)
        
        return result
    
    def _save_batch(original_data, items, f):
        try:
            for i, item in enumerate(items):
                train_type = item.get("_train_type")
                if train_type and train_type in original_data:
                    type_list = original_data[train_type]
                    original_idx = None
                    for j, orig_item in enumerate(type_list):
                        if orig_item.get("source_file") == item.get("source_file") and \
                           orig_item.get("train_data") == item.get("train_data"):
                            original_idx = j
                            break
                    if original_idx is not None and "embedding" in item:
                        type_list[original_idx]["embedding"] = item["embedding"]
            
            with open(f, "w", encoding="utf-8") as file:
                json.dump(original_data, file, ensure_ascii=False, indent=2)
        except:
            pass
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_vectorize_one, item): item for item in to_vectorize}
        
        for future in as_completed(futures):
            idx, embedding, error = future.result()
            if embedding:
                all_items[idx]["embedding"] = embedding
            elif error:
                print(f"\n数据 {idx} 向量化失败: {error}")
    
    for item in all_items:
        train_type = item.pop("_train_type", None)
        if train_type and train_type in data:
            type_list = data[train_type]
            for j, orig_item in enumerate(type_list):
                if orig_item.get("source_file") == item.get("source_file") and \
                   orig_item.get("train_data") == item.get("train_data"):
                    if "embedding" in item:
                        type_list[j]["embedding"] = item["embedding"]
                    break
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n向量化完成，共处理 {completed[0]} 条数据")
    
    return data


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    arr1 = np.array(vec1)
    arr2 = np.array(vec2)
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def find_similar_items(json_file: str, threshold: float = 0.85) -> List[Dict[str, Any]]:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_items = []
    for train_type in ["知识易错训练", "套路反射训练"]:
        for item in data.get(train_type, []):
            item["_train_type"] = train_type
            all_items.append(item)
    
    items_with_embedding = [(i, item) for i, item in enumerate(all_items) if "embedding" in item]
    
    similar_pairs = []
    n = len(items_with_embedding)
    
    print(f"正在查找相似项，共 {n} 条数据...")
    
    for i in range(n):
        for j in range(i + 1, n):
            idx1, item1 = items_with_embedding[i]
            idx2, item2 = items_with_embedding[j]
            
            if item1.get("_train_type") != item2.get("_train_type"):
                continue
            
            similarity = cosine_similarity(item1["embedding"], item2["embedding"])
            
            if similarity >= threshold:
                train_type = item1.get("_train_type", "")
                similar_pairs.append({
                    "index1": idx1,
                    "index2": idx2,
                    "train_type": train_type,
                    "similarity": similarity,
                    "item1": item1,
                    "item2": item2
                })
    
    print(f"找到 {len(similar_pairs)} 对相似项")
    return similar_pairs


KNOWLEDGE_ERROR_MERGE_PROMPT = """你是一个数学教育专家，专门负责判断"知识易错训练"题目是否应该合并。

判断是否合并的标准：
1. 如果两个题目考查的知识点完全相同，只是表述不同，应该合并
2. 如果两个题目的答案核心内容相同，可以合并
3. 如果两个题目考查不同知识点，不应合并
4. 合并后的题目应该保留更完整、更清晰的表述

返回JSON格式：
{
  "should_merge": true/false,
  "reason": "合并或不合并的原因",
  "merged_train_content": "合并后的题目内容（如果合并）",
  "merged_answer": "合并后的答案（如果合并）",
  "merged_train_form": "合并后的题目形式（如果合并）"
}"""


PATTERN_REFLEX_MERGE_PROMPT = """你是一个数学教育专家，专门负责判断"套路反射训练"题目是否应该合并。

判断是否合并的标准：
1. 如果两个题目考查的解题套路完全相同，只是表述不同，应该合并
2. 如果两个题目的标准答案核心内容相同，可以合并
3. 如果两个题目考查不同的解题套路，不应合并
4. 合并后的题目应该保留更完整、更清晰的表述，并整合"高考得分点"、"同类题型拓展"、"高考高频考法"等内容

返回JSON格式：
{
  "should_merge": true/false,
  "reason": "合并或不合并的原因",
  "merged_question": "合并后的题目（如果合并）",
  "merged_standard_answer": "合并后的标准答案（如果合并）"
}"""


def merge_similar_items(similar_pairs: List[Dict[str, Any]], max_workers: int = 3) -> List[Dict[str, Any]]:
    ai = AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.high,
        max_output_tokens=131072
    )
    
    total = len(similar_pairs)
    if total == 0:
        return []
    
    print(f"需要处理 {total} 对相似项")
    
    print_lock = threading.Lock()
    completed = [0]
    merge_results = [None] * total
    
    def _merge_one(index, pair):
        train_type = pair.get("train_type", "")
        item1 = pair.get("item1", {})
        item2 = pair.get("item2", {})
        train_data1 = item1.get("train_data", {})
        train_data2 = item2.get("train_data", {})
        
        if train_type == "知识易错训练":
            system_prompt = KNOWLEDGE_ERROR_MERGE_PROMPT
            user_text = f"""请判断以下两个"知识易错训练"题目是否应该合并：

题目1：
- 形式：{train_data1.get("train_form", "")}
- 内容：{train_data1.get("train_content", "")}
- 答案：{train_data1.get("answer", "")}

题目2：
- 形式：{train_data2.get("train_form", "")}
- 内容：{train_data2.get("train_content", "")}
- 答案：{train_data2.get("answer", "")}

相似度：{pair.get("similarity", 0):.4f}

请返回JSON格式的判断结果。"""
        else:
            system_prompt = PATTERN_REFLEX_MERGE_PROMPT
            user_text = f"""请判断以下两个"套路反射训练"题目是否应该合并：

题目1：
- 问题：{train_data1.get("question", "")}
- 标准答案：{train_data1.get("standard_answer", "")}

题目2：
- 问题：{train_data2.get("question", "")}
- 标准答案：{train_data2.get("standard_answer", "")}

相似度：{pair.get("similarity", 0):.4f}

请返回JSON格式的判断结果。"""
        
        try:
            result = call_ai_json(
                ai=ai,
                system_prompt=system_prompt,
                user_content=build_input_content(user_text)
            )
            merge_result = {
                "original_pair": pair,
                "merge_decision": result
            }
        except Exception as e:
            merge_result = {
                "original_pair": pair,
                "merge_decision": {"should_merge": False, "reason": str(e)}
            }
        
        with print_lock:
            completed[0] += 1
            print(f"\rAI合并进度: {completed[0]}/{total}", end="", flush=True)
        
        return index, merge_result
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_merge_one, i, pair): i for i, pair in enumerate(similar_pairs)}
        
        for future in as_completed(futures):
            idx, result = future.result()
            merge_results[idx] = result
    
    print(f"\nAI合并完成，共处理 {completed[0]} 对题目")
    
    return merge_results


def save_merged_items(json_file: str, merge_results: List[Dict[str, Any]]) -> None:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    merged_count = 0
    
    for result in merge_results:
        merge_decision = result.get("merge_decision", {})
        if isinstance(merge_decision, str):
            try:
                merge_decision = json.loads(merge_decision)
            except:
                continue
        if not isinstance(merge_decision, dict):
            continue
        if merge_decision.get("should_merge", False):
            original_pair = result.get("original_pair", {})
            train_type = original_pair.get("train_type", "")
            
            if train_type == "知识易错训练":
                merged_item = {
                    "source_file": "merged",
                    "unit_content": original_pair.get("item1", {}).get("unit_content", ""),
                    "classify_result": original_pair.get("item1", {}).get("classify_result", ""),
                    "train_data": {
                        "train_type": "知识易错训练",
                        "train_form": merge_decision.get("merged_train_form", ""),
                        "train_content": merge_decision.get("merged_train_content", ""),
                        "answer": merge_decision.get("merged_answer", "")
                    },
                    "merged_from": [
                        original_pair.get("index1"),
                        original_pair.get("index2")
                    ]
                }
                data["知识易错训练"].append(merged_item)
            elif train_type == "套路反射训练":
                merged_item = {
                    "source_file": "merged",
                    "unit_content": original_pair.get("item1", {}).get("unit_content", ""),
                    "classify_result": original_pair.get("item1", {}).get("classify_result", ""),
                    "train_data": {
                        "train_type": "套路反射训练",
                        "question": merge_decision.get("merged_question", ""),
                        "standard_answer": merge_decision.get("merged_standard_answer", "")
                    },
                    "merged_from": [
                        original_pair.get("index1"),
                        original_pair.get("index2")
                    ]
                }
                data["套路反射训练"].append(merged_item)
            
            merged_count += 1
    
    data["统计"]["知识易错训练数量"] = len(data.get("知识易错训练", []))
    data["统计"]["套路反射训练数量"] = len(data.get("套路反射训练", []))
    data["统计"]["总数量"] = data["统计"]["知识易错训练数量"] + data["统计"]["套路反射训练数量"]
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"保存完成，共合并 {merged_count} 对题目")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="训练数据相似项合并工具")
    parser.add_argument("--vectorize", action="store_true", help="执行向量化")
    parser.add_argument("--find-similar", action="store_true", help="查找相似项")
    parser.add_argument("--merge", action="store_true", help="AI合并相似项")
    parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值，默认0.85")
    parser.add_argument("--json-file", type=str, default="extracted_train_data.json", help="JSON文件路径")
    parser.add_argument("--workers", type=int, default=5, help="向量化并发数，默认5")
    parser.add_argument("--merge-workers", type=int, default=3, help="AI合并并发数，默认3")
    
    args = parser.parse_args()
    
    if args.vectorize:
        print(f"开始向量化 (并发数: {args.workers})...")
        vectorize_train_data(args.json_file, max_workers=args.workers)
    
    elif args.find_similar:
        print(f"查找相似项 (阈值: {args.threshold})...")
        similar_pairs = find_similar_items(args.json_file, args.threshold)
        print(f"找到 {len(similar_pairs)} 对相似项")
        for i, pair in enumerate(similar_pairs[:10], 1):
            print(f"\n第 {i} 对 (相似度: {pair['similarity']:.4f}, 类型: {pair['train_type']}):")
            train_data1 = pair['item1'].get('train_data', {})
            train_data2 = pair['item2'].get('train_data', {})
            if pair['train_type'] == "知识易错训练":
                print(f"  题目1: {train_data1.get('train_content', '')[:50]}...")
                print(f"  题目2: {train_data2.get('train_content', '')[:50]}...")
            else:
                print(f"  题目1: {train_data1.get('question', '')[:50]}...")
                print(f"  题目2: {train_data2.get('question', '')[:50]}...")
    
    elif args.merge:
        print(f"AI合并相似项 (阈值: {args.threshold}, 并发数: {args.merge_workers})...")
        similar_pairs = find_similar_items(args.json_file, args.threshold)
        if not similar_pairs:
            print("没有找到相似项")
        else:
            merge_results = merge_similar_items(similar_pairs, max_workers=args.merge_workers)
            save_merged_items(args.json_file, merge_results)
    
    else:
        parser.print_help()
