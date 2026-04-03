import json
import os
import argparse
from ai.question_vectorizer import (
    vectorize_questions, 
    find_similar_questions, 
    merge_similar_questions,
    save_merged_questions
)
from ai.base import AI

def parse_judgment_questions(text):
    """
    解析判断题字符串
    格式: 题目|||答案 &&& 题目|||答案
    """
    questions_list = []
    
    questions = text.split("&&&")
    
    for q in questions:
        q = q.strip()
        if not q:
            continue
        
        if "|||" in q:
            parts = q.split("|||", 1)
            question = parts[0].strip()
            answer = parts[1].strip() if len(parts) > 1 else ""
            
            questions_list.append({
                "question": question,
                "answer": answer
            })
    
    return questions_list

def save_to_json_incremental(questions_list, json_file="judgment_questions.json"):
    """
    增量保存判断题到JSON文件
    """
    existing_data = []
    
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = []
    
    existing_questions = {q["question"] for q in existing_data}
    
    new_count = 0
    for q in questions_list:
        if q["question"] not in existing_questions:
            existing_data.append(q)
            existing_questions.add(q["question"])
            new_count += 1
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"新增 {new_count} 条记录，总共 {len(existing_data)} 条记录")
    return existing_data

def read_text_from_file(file_path):
    """
    从txt文件读取内容
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return ""
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="判断题处理工具")
    parser.add_argument("--vectorize", action="store_true", help="执行向量化")
    parser.add_argument("--find-similar", action="store_true", help="查找相似题目")
    parser.add_argument("--merge", action="store_true", help="AI合并相似题目")
    parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值，默认0.85")
    parser.add_argument("--json-file", type=str, default="judgment_questions.json", help="JSON文件路径")
    parser.add_argument("--workers", type=int, default=5, help="向量化并发数，默认5")
    parser.add_argument("--merge-workers", type=int, default=3, help="AI合并并发数，默认3")
    
    args = parser.parse_args()
    
    if args.vectorize:
        print(f"开始向量化 (并发数: {args.workers})...")
        vectorize_questions(args.json_file, max_workers=args.workers)
    
    elif args.find_similar:
        print(f"查找相似题目 (阈值: {args.threshold})...")
        similar_pairs = find_similar_questions(args.json_file, args.threshold)
        print(f"找到 {len(similar_pairs)} 对相似题目")
        for i, pair in enumerate(similar_pairs, 1):
            print(f"\n第 {i} 对 (相似度: {pair['similarity']:.4f}):")
            print(f"  题目1: {pair['question1'][:50]}...")
            print(f"  题目2: {pair['question2'][:50]}...")
    
    elif args.merge:
        print(f"AI合并相似题目 (阈值: {args.threshold}, 并发数: {args.merge_workers})...")
        similar_pairs = find_similar_questions(args.json_file, args.threshold)
        if not similar_pairs:
            print("没有找到相似题目")
        else:
            ai = AI()
            merge_results = merge_similar_questions(similar_pairs, ai, max_workers=args.merge_workers)
            save_merged_questions(args.json_file, merge_results)
            merged_count = sum(1 for r in merge_results if r.get("merge_decision", {}).get("should_merge", False))
            print(f"合并完成，共合并 {merged_count} 对题目")
    
    else:
        txt_file = "judgment_questions.txt"
        sample_text = read_text_from_file(txt_file)
        
        if not sample_text:
            print("txt文件为空或不存在")
            exit(1)
        
        questions = parse_judgment_questions(sample_text)
        
        print("解析结果:")
        for i, q in enumerate(questions, 1):
            print(f"{i}. 题目: {q['question']}")
        
        all_data = save_to_json_incremental(questions)
