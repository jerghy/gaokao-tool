# 化学难点详细教学AI生成功能实现计划

## 需求概述

对标签为"化学"且 `selected_difficulty_ids` 有数据的题目，根据用户选择的难点ID，生成详细的难点攻克教学内容。

- **提示词文件**: `d:\space\html\print\ai\tsc\化学难点.txt`
- **模型**: `doubao-seed-2-0-pro-260215`
- **推理深度**: `medium`
- **输出字段**: `difficulty_teaching` (Markdown内容)
- **目标题目**: 标签为"化学"且 `selected_difficulty_ids` 有数据的题目

## 数据结构说明

```json
{
  "chemistry_preprocessing": {
    "Difficulties": [
      {
        "DifficultyID": 1,
        "DifficultyName": "...",
        "BreakthroughSolution": "...",
        ...
      },
      {
        "DifficultyID": 2,
        ...
      }
    ]
  },
  "selected_difficulty_ids": [1],  // 用户选择的难点ID
  "difficulty_teaching": {         // 新增字段，存储生成的教学内容
    "1": "# 整体学习目标\n..."     // key为DifficultyID，value为Markdown内容
  }
}
```

## 处理逻辑

1. 筛选条件：
   - 标签包含"化学"
   - `chemistry_preprocessing` 字段存在
   - `selected_difficulty_ids` 数组非空
   
2. 对于每个 `selected_difficulty_ids` 中的ID：
   - 从 `chemistry_preprocessing.Difficulties` 中找到对应难点
   - 调用AI生成该难点的详细教学内容
   - 保存到 `difficulty_teaching[difficulty_id]` 字段

3. 输入给AI的内容：
   - 原题内容（题干、选项、答案）
   - 单个难点单元的完整JSON

---

## 实现步骤

### 步骤1：创建化学难点教学处理器模块

**文件**: `d:\space\html\print\ai\chemistry_difficulty_processor.py`

**核心功能**:
- 加载化学难点提示词
- 构建输入内容（题目 + 单个难点JSON）
- 调用AI生成Markdown教学内容
- 解析并保存到题目文件

**核心代码结构**:
```python
@dataclass
class DifficultyTeaching:
    difficulty_id: int
    content: str  # Markdown内容
    raw_response: str

def get_difficulty_prompt() -> str:
    # 从文件加载提示词
    
def build_difficulty_input(question_text, answer_text, difficulty_json) -> str:
    # 构建输入内容
    
def generate_difficulty_teaching(question, difficulty, ai, ...) -> DifficultyTeaching:
    # 调用AI生成
    
def process_difficulty_for_question(data_dir, question_id, difficulty_id, ...) -> Optional[DifficultyTeaching]:
    # 处理单个题目的单个难点
    
def batch_process_difficulties(data_dir, max_workers) -> dict:
    # 批量处理所有符合条件的题目
```

### 步骤2：更新 `ai/__init__.py`

导出新增的难点处理器函数和类。

### 步骤3：创建批处理脚本

**文件**: `d:\space\html\print\batch_chemistry_difficulty.py`

---

## 详细代码设计

### 1. `ai/chemistry_difficulty_processor.py`

```python
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
) -> DifficultyTeaching:
    base_ai = ai or AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
    )
    final_ai = base_ai.with_overrides(api_key=api_key)
    
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
    skip_if_exists: bool = True,
) -> Optional[DifficultyTeaching]:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 检查是否已存在
    if skip_if_exists:
        existing = data.get("difficulty_teaching", {})
        if str(difficulty_id) in existing:
            return None
    
    # 获取难点数据
    preprocessing = data.get("chemistry_preprocessing", {})
    difficulties = preprocessing.get("Difficulties", [])
    
    target_difficulty = None
    for d in difficulties:
        if d.get("DifficultyID") == difficulty_id:
            target_difficulty = d
            break
    
    if not target_difficulty:
        return None
    
    # 加载题目
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    
    # 生成教学内容
    result = generate_difficulty_teaching(question, target_difficulty, ai, api_key)
    
    # 保存
    if "difficulty_teaching" not in data:
        data["difficulty_teaching"] = {}
    data["difficulty_teaching"][str(difficulty_id)] = result.content
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return result


def get_questions_with_selected_difficulties(data_dir: str) -> list[dict]:
    """获取所有需要处理难点教学的题目"""
    questions = []
    
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        
        file_path = os.path.join(data_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 检查标签
        tags = data.get("tags", [])
        if "化学" not in tags:
            continue
        
        # 检查是否有chemistry_preprocessing
        preprocessing = data.get("chemistry_preprocessing", {})
        if not preprocessing:
            continue
        
        # 检查是否有selected_difficulty_ids
        selected_ids = data.get("selected_difficulty_ids", [])
        if not selected_ids:
            continue
        
        # 获取未处理的难点ID
        existing_teaching = data.get("difficulty_teaching", {})
        pending_ids = [i for i in selected_ids if str(i) not in existing_teaching]
        
        if pending_ids:
            questions.append({
                "id": filename.replace(".json", ""),
                "pending_difficulty_ids": pending_ids,
            })
    
    return questions


def batch_process_difficulties(
    data_dir: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    max_workers: int = 3,
) -> dict:
    questions = get_questions_with_selected_difficulties(data_dir)
    
    # 展开为单个任务
    tasks = []
    for q in questions:
        for diff_id in q["pending_difficulty_ids"]:
            tasks.append({
                "question_id": q["id"],
                "difficulty_id": diff_id,
            })
    
    total = len(tasks)
    results = {"total": total, "success": [], "failed": []}
    
    print(f"发现 {len(questions)} 个题目，共 {total} 个难点需要生成教学内容")
    print(f"并发数: {max_workers}")
    print("=" * 60)
    
    if total == 0:
        return results
    
    def _process_one(task, index):
        result = {"question_id": task["question_id"], "difficulty_id": task["difficulty_id"], "success": False}
        try:
            teaching = process_difficulty_for_question(
                data_dir, task["question_id"], task["difficulty_id"], ai, api_key
            )
            if teaching:
                result["success"] = True
        except Exception as e:
            result["error"] = str(e)[:100]
        
        with print_lock:
            status = "✓" if result["success"] else "✗"
            print(f"[{index}/{total}] {status} {task['question_id']} - 难点{task['difficulty_id']}")
        
        return result
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, t, i): t for i, t in enumerate(tasks, 1)}
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result)
            else:
                results["failed"].append(result)
    
    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")
    
    return results
```

---

## 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `ai/chemistry_difficulty_processor.py` | 新建 | 化学难点教学处理器核心模块 |
| `ai/__init__.py` | 修改 | 导出难点处理器 |
| `batch_chemistry_difficulty.py` | 新建 | 批处理脚本 |

---

## 使用方式

```bash
# 运行批处理
python batch_chemistry_difficulty.py
```

或在代码中调用：
```python
from ai import batch_process_difficulties, process_difficulty_for_question

# 处理单个题目的单个难点
process_difficulty_for_question("data", "20260321144724", difficulty_id=1)

# 批量处理
batch_process_difficulties("data", max_workers=3)
```

---

## 输出示例

处理后的题目JSON将新增 `difficulty_teaching` 字段：
```json
{
  "id": "20260321144724",
  "selected_difficulty_ids": [1],
  "difficulty_teaching": {
    "1": "# 整体学习目标\n\n学完本内容，你将彻底掌握pc-pH沉淀溶解曲线的离子归属与信息提取方法...\n\n## 模块一：难点前置校验与学习指引\n..."
  }
}
```
