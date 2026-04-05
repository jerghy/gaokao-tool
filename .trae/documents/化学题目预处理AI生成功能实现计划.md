# 化学题目预处理AI生成功能实现计划

## 需求概述

利用现有AI系统，对标签为"化学"的题目进行AI生成处理：
- **提示词文件**: `d:\space\html\print\ai\tsc\化学题目预处理.txt`
- **模型**: `doubao-seed-2-0-pro-260215`
- **推理深度**: `medium`
- **输出字段**: `chemistry_preprocessing` (AI生成的JSON数据)
- **目标题目**: 标签包含"化学"的题目

## 输出JSON结构

根据提示词要求，AI输出格式为：
```json
{
  "Accumulation": [...],
  "Difficulties": [...]
}
```

## 实现方案

### 方案选择：创建专用处理器模块

参考现有 `ai/preprocessor.py` 和 `ai/generic_processor.py` 的模式，创建化学专用处理器。

---

## 实现步骤

### 步骤1：创建化学预处理器模块

**文件**: `d:\space\html\print\ai\chemistry_processor.py`

**功能**:
- 加载化学预处理提示词
- 调用AI生成化学题目分析
- 解析JSON结果并保存到题目文件

**核心代码结构**:
```python
@dataclass
class ChemistryPreprocessing:
    Accumulation: list
    Difficulties: list
    raw_response: str

def get_chemistry_prompt() -> str:
    # 从文件加载提示词
    
def generate_chemistry_preprocessing(question, ai, ...) -> ChemistryPreprocessing:
    # 调用AI生成
    
def process_chemistry_question(data_dir, question_id, ...) -> Optional[ChemistryPreprocessing]:
    # 处理单个题目并保存
```

### 步骤2：更新 `ai/__init__.py`

导出新增的化学处理器函数和类。

### 步骤3：创建批处理脚本

**文件**: `d:\space\html\print\batch_chemistry_preprocess.py`

**功能**:
- 搜索标签为"化学"的题目
- 筛选未处理的题目（无 `chemistry_preprocessing` 字段）
- 并发批量处理
- 输出处理统计

**核心逻辑**:
```python
def get_chemistry_questions_without_preprocessing(data_dir) -> list[str]:
    # 获取标签为"化学"且未处理的题目ID列表
    
def batch_process_chemistry(data_dir, max_workers=3) -> dict:
    # 批量处理
```

---

## 详细代码设计

### 1. `ai/chemistry_processor.py`

```python
import os
import json
from typing import Optional, Union
from dataclasses import dataclass

from ai.base import AI, ReasoningEffort, call_ai, build_input_content
from ai.loader import ProcessedQuestion, load_question_by_id

__all__ = [
    "ChemistryPreprocessing",
    "get_chemistry_prompt",
    "generate_chemistry_preprocessing",
    "process_chemistry_question",
    "batch_process_chemistry",
]

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "tsc", "化学题目预处理.txt")

@dataclass
class ChemistryPreprocessing:
    Accumulation: list
    Difficulties: list
    raw_response: str
    
    def to_dict(self) -> dict:
        return {
            "Accumulation": self.Accumulation,
            "Difficulties": self.Difficulties
        }

def get_chemistry_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def generate_chemistry_preprocessing(
    question: ProcessedQuestion,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
) -> ChemistryPreprocessing:
    # 配置AI参数
    base_ai = ai or AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
    )
    final_ai = base_ai.with_overrides(api_key=api_key)
    
    # 构建提示
    prompt_text = f"""请对以下化学题目进行预处理分析：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}
"""
    
    # 调用AI
    user_content = build_input_content(prompt_text, question.image_paths)
    raw_response = call_ai(final_ai, get_chemistry_prompt(), user_content)
    
    # 解析JSON
    result = parse_json_result(raw_response)
    
    return ChemistryPreprocessing(
        Accumulation=result.get("Accumulation", []),
        Difficulties=result.get("Difficulties", []),
        raw_response=raw_response
    )

def process_chemistry_question(
    data_dir: str,
    question_id: str,
    ai: Optional[AI] = None,
    api_key: Optional[str] = None,
    skip_if_exists: bool = True,
) -> Optional[ChemistryPreprocessing]:
    # 加载题目
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    
    # 检查是否已存在
    file_path = os.path.join(data_dir, f"{question_id}.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if skip_if_exists and "chemistry_preprocessing" in data:
        return None
    
    # 生成并保存
    result = generate_chemistry_preprocessing(question, ai, api_key)
    
    data["chemistry_preprocessing"] = result.to_dict()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return result
```

### 2. `batch_chemistry_preprocess.py`

```python
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.chemistry_processor import process_chemistry_question
from ai.base import AI, ReasoningEffort

data_dir = r"d:\space\html\print\data"
os.environ["ARK_API_KEY"] = "your-api-key"

print_lock = threading.Lock()

def get_chemistry_questions_without_preprocessing(data_dir: str) -> list[str]:
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
        
        # 检查是否已处理
        if "chemistry_preprocessing" in data:
            continue
        
        questions.append(filename.replace(".json", ""))
    
    return questions

def process_single(question_id: str, index: int, total: int) -> dict:
    result = {"id": question_id, "success": False, "message": ""}
    
    try:
        ai = AI(
            model="doubao-seed-2-0-pro-260215",
            reasoning_effort=ReasoningEffort.medium,
        )
        preprocessing = process_chemistry_question(data_dir, question_id, ai=ai)
        
        if preprocessing:
            result["success"] = True
            result["message"] = f"Accumulation: {len(preprocessing.Accumulation)}条, Difficulties: {len(preprocessing.Difficulties)}条"
        else:
            result["message"] = "已存在或题目不存在"
    except Exception as e:
        result["message"] = str(e)[:100]
    
    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {question_id}: {result['message'][:50]}")
    
    return result

def batch_process_chemistry(data_dir: str, max_workers: int = 3) -> dict:
    questions = get_chemistry_questions_without_preprocessing(data_dir)
    total = len(questions)
    
    results = {"total": total, "success": [], "failed": [], "skipped": []}
    
    print(f"发现 {total} 个化学题目需要预处理")
    print(f"并发数: {max_workers}")
    print("=" * 60)
    
    if total == 0:
        return results
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single, qid, i, total): qid
            for i, qid in enumerate(questions, 1)
        }
        
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["success"].append(result["id"])
            elif "已存在" in result["message"]:
                results["skipped"].append(result["id"])
            else:
                results["failed"].append({"id": result["id"], "reason": result["message"]})
    
    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")
    
    return results

if __name__ == "__main__":
    batch_process_chemistry(data_dir, max_workers=3)
```

---

## 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `ai/chemistry_processor.py` | 新建 | 化学预处理器核心模块 |
| `ai/__init__.py` | 修改 | 导出化学处理器 |
| `batch_chemistry_preprocess.py` | 新建 | 批处理脚本 |

---

## 使用方式

```bash
# 运行批处理
python batch_chemistry_preprocess.py
```

或在代码中调用：
```python
from ai.chemistry_processor import process_chemistry_question, batch_process_chemistry

# 处理单个题目
process_chemistry_question("data", "20260314093233")

# 批量处理
batch_process_chemistry("data", max_workers=3)
```

---

## 输出示例

处理后的题目JSON将包含新字段：
```json
{
  "id": "20260314093233",
  "tags": ["化学", "知识点::电化学"],
  "question": {...},
  "answer": {...},
  "chemistry_preprocessing": {
    "Accumulation": [
      {
        "ExerciseType": "判断题",
        "ExamTag": "选择性必修1-电化学-原电池离子迁移规律",
        "AdaptScore": "中段60-80分",
        "ExerciseContent": "...",
        "AnswerAnalysis": "..."
      }
    ],
    "Difficulties": [
      {
        "DifficultyID": 1,
        "ExamTag": "选择性必修1-电化学-双电解液电池电极反应式书写",
        "DifficultyName": "...",
        "DifficultyLevel": 4,
        "BreakthroughValue": 5,
        "ProcessPriority": "最高",
        "QuestionAnchor": "...",
        "BreakthroughSolution": "..."
      }
    ]
  }
}
```
