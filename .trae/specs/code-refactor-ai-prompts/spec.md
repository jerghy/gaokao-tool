# 代码模块化重构 - AI提示词分离

## Why
现有代码中AI提示词（SYSTEM_PROMPT）直接写在Python文件中，与业务逻辑混杂，导致：
1. 代码阅读障碍 - 业务逻辑和长字符串混杂
2. 提示词难以复用和维护
3. prompt_v1/v2两套系统并存，结构不统一

## What Changes
- 创建 `d:\space\html\print\ai\` 目录
- 将AI提示词抽取为独立的 `prompts.py` 文件，每个提示词一个函数
- 重新组织代码结构，将核心逻辑与API调用分离
- 删除原有的5个Python文件：`question_preprocessor.py`, `question_preprocessor_v2.py`, `question_loader.py`, `question_evaluator.py`, `batch_preprocess.py`

## Impact
- **新增目录**: `d:\space\html\print\ai\`
- **新增文件**:
  - `prompts.py` - 所有AI提示词函数
  - `loader.py` - 题目加载逻辑
  - `evaluator.py` - 题目质量评估（调用prompts）
  - `preprocessor.py` - 题目预处理（调用prompts）
  - `batch_processor.py` - 批量处理逻辑
  - `__init__.py` - 包导出
- **删除文件**: 原有5个py文件

## ADDED Requirements

### Requirement: prompts.py 提示词模块化
prompts.py 必须导出以下函数：
- `get_neural_reaction_prompt()` - 返回神经刺激式积累反应提示词（对应原question_preprocessor.py）
- `get_preprocessing_prompt_v2()` - 返回全维度题目预处理提示词（对应原question_preprocessor_v2.py）
- `get_evaluation_prompt()` - 返回题目质量判定提示词（对应原question_evaluator.py）

#### Scenario: 调用提示词函数
- **WHEN** 业务代码调用 `prompts.get_neural_reaction_prompt()`
- **THEN** 返回完整的SYSTEM_PROMPT字符串，无任何业务逻辑

### Requirement: loader.py 题目加载模块
loader.py 必须导出：
- `ProcessedQuestion` dataclass
- `load_question_by_id(data_dir, question_id)` 函数
- `load_question_from_file(file_path)` 函数

### Requirement: preprocessor.py 预处理模块
preprocessor.py 必须导出：
- `QuestionAnalysis` dataclass
- `generate_question_analysis(question, api_key, model)` 函数
- `preprocess_and_save(data_dir, question_id, api_key, model)` 函数

### Requirement: evaluator.py 评估模块
evaluator.py 必须导出：
- `QualityEvaluation` dataclass
- `evaluate_question_quality(question, api_key, model)` 函数
- `evaluate_and_save(data_dir, question_id, api_key, model)` 函数

### Requirement: batch_processor.py 批量处理模块
batch_processor.py 必须导出：
- `batch_process(data_dir, tags, require_all_tags, max_workers)` 函数
- `get_questions_without_reaction(data_dir, tags, require_all_tags)` 函数

## MODIFIED Requirements

### Requirement: API调用逻辑保持不变
- 使用 `volcenginesdkarkruntime.Ark` 作为API客户端
- 支持图片base64编码
- 支持 `thinking={"type": "enabled"}` 参数
- 默认model: `doubao-seed-2-0-pro-260215`

## REMOVED Requirements
### Requirement: 原question_preprocessor.py
**Reason**: 功能已重构到新的ai/preprocessor.py，提示词已抽取到ai/prompts.py
**Migration**: 使用新的 `from ai.preprocessor import preprocess_and_save`

### Requirement: 原question_preprocessor_v2.py
**Reason**: 功能已重构到新的ai/preprocessor.py（统一版本），提示词已抽取到ai/prompts.py
**Migration**: 使用新的 `from ai.preprocessor import preprocess_and_save`

### Requirement: 原question_evaluator.py
**Reason**: 功能已重构到新的ai/evaluator.py，提示词已抽取到ai/prompts.py
**Migration**: 使用新的 `from ai.evaluator import evaluate_and_save`

### Requirement: 原question_loader.py
**Reason**: 功能已重构到新的ai/loader.py
**Migration**: 使用新的 `from ai.loader import load_question_by_id`

### Requirement: 原batch_preprocess.py
**Reason**: 功能已重构到新的ai/batch_processor.py
**Migration**: 使用新的 `from ai.batch_processor import batch_process`

## 目录结构

```
d:\space\html\print\ai\
├── __init__.py          # 包导出，所有公共接口
├── prompts.py           # AI提示词函数
├── loader.py            # 题目加载
├── evaluator.py         # 题目质量评估
├── preprocessor.py      # 题目预处理
└── batch_processor.py  # 批量处理
```
