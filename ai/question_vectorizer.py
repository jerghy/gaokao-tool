import os
import json
import threading
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from volcenginesdkarkruntime import Ark

from ai.base import AI, call_ai_json, build_input_content


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


def vectorize_questions(json_file: str, max_workers: int = 5, batch_save: int = 10) -> List[dict]:
    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    to_vectorize = []
    for i, question in enumerate(questions):
        if "embedding" not in question:
            question_text = question.get("question", "")
            if question_text:
                to_vectorize.append((i, question_text))
    
    if not to_vectorize:
        print("所有题目已向量化，无需处理")
        return questions
    
    total = len(to_vectorize)
    print(f"需要向量化的题目: {total} 道")
    
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
                _save_batch(questions, json_file)
        
        return result
    
    def _save_batch(qs, f):
        try:
            with open(f, "w", encoding="utf-8") as file:
                json.dump(qs, file, ensure_ascii=False, indent=2)
        except:
            pass
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_vectorize_one, item): item for item in to_vectorize}
        
        for future in as_completed(futures):
            idx, embedding, error = future.result()
            if embedding:
                questions[idx]["embedding"] = embedding
            elif error:
                print(f"\n题目 {idx} 向量化失败: {error}")
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n向量化完成，共处理 {completed[0]} 道题目")
    
    return questions


def save_embeddings(json_file: str, questions: List[dict]) -> None:
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    arr1 = np.array(vec1)
    arr2 = np.array(vec2)
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def find_similar_questions(json_file: str, threshold: float = 0.85) -> List[dict]:
    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    questions_with_embedding = [(i, q) for i, q in enumerate(questions) if "embedding" in q]
    
    similar_pairs = []
    n = len(questions_with_embedding)
    
    for i in range(n):
        for j in range(i + 1, n):
            idx1, q1 = questions_with_embedding[i]
            idx2, q2 = questions_with_embedding[j]
            
            similarity = cosine_similarity(q1["embedding"], q2["embedding"])
            
            if similarity >= threshold:
                similar_pairs.append({
                    "index1": idx1,
                    "index2": idx2,
                    "similarity": similarity,
                    "question1": q1.get("question", ""),
                    "question2": q2.get("question", ""),
                    "answer1": q1.get("answer", ""),
                    "answer2": q2.get("answer", "")
                })
    
    return similar_pairs


MERGE_PROMPT = """你是一个生物学判断题专家。你的任务是判断两个相似的判断题是否应该合并，如果应该合并，生成合并后的题目和答案。

判断是否合并的标准：
1. 如果两个题目考查的知识点完全相同，只是表述不同，应该合并
2. 如果两个题目答案相同且互为补充，可以合并
3. 如果两个题目考查不同知识点，不应合并

返回JSON格式：
{
  "should_merge": true/false,
  "reason": "合并或不合并的原因",
  "merged_question": "合并后的题目（如果合并）",
  "merged_answer": "合并后的答案（如果合并）"
}"""


def merge_similar_questions(similar_pairs: List[dict], ai: AI = None, max_workers: int = 5) -> List[dict]:
    if ai is None:
        ai = AI()
    
    total = len(similar_pairs)
    if total == 0:
        return []
    
    print(f"需要处理 {total} 对相似题目")
    
    print_lock = threading.Lock()
    completed = [0]
    merge_results = [None] * total
    
    def _merge_one(index, pair):
        user_text = f"""请判断以下两个判断题是否应该合并：

题目1：{pair.get("question1", "")}
答案1：{pair.get("answer1", "")}

题目2：{pair.get("question2", "")}
答案2：{pair.get("answer2", "")}

相似度：{pair.get("similarity", 0):.4f}

请返回JSON格式的判断结果。"""
        
        try:
            result = call_ai_json(
                ai=ai,
                system_prompt=MERGE_PROMPT,
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


def save_merged_questions(json_file: str, merge_results: List[dict]) -> None:
    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    for result in merge_results:
        merge_decision = result.get("merge_decision", {})
        if merge_decision.get("should_merge", False):
            original_pair = result.get("original_pair", {})
            merged_question = {
                "question": merge_decision.get("merged_question", ""),
                "answer": merge_decision.get("merged_answer", ""),
                "merged_from": [
                    original_pair.get("index1"),
                    original_pair.get("index2")
                ]
            }
            questions.append(merged_question)
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
