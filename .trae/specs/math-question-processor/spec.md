# 高中数学题目处理器 Spec

## Why
当前需要实现一个专门处理高中数学题目的AI处理器，根据伪代码 `math.py` 中定义的流程：
1. 使用第一个AI提示词完成题目的最小单元拆分、分类和基础预处理
2. 对"思维提升类"题目调用第二个AI提示词进行深度拆解
3. 将最终结果保存到原JSON文件中

现有代码已有 `thinking_processor.py`、`immersion_processor.py` 等类似处理器，但缺少专门针对数学题目的两阶段处理流程。

## What Changes
- 新增 `ai/math_processor.py` 实现数学题目处理核心逻辑
- 新增提示词加载函数，从 `ai/tsc/` 目录加载txt格式的提示词
- 实现两阶段处理流程：拆分分类预处理 → 思维提升类深度拆解
- 支持按题目ID处理并保存结果到原JSON

## Impact
- Affected code: `ai/math.py`（伪代码转实现）
- Affected files: `ai/tsc/Math_Topic_Split_Classify_Preprocess_Prompt.txt`, `ai/tsc/Math_Thinking_Chain_Deep_Parse_Prompt.txt`
- 向后兼容：纯新增功能

## ADDED Requirements

### Requirement: 提示词加载功能
系统 SHALL 提供从txt文件加载提示词的功能

#### Scenario: 加载数学题目处理提示词
- **WHEN** 调用 `load_math_prompt("Math_Topic_Split_Classify_Preprocess_Prompt")`
- **THEN** 返回 `ai/tsc/Math_Topic_Split_Classify_Preprocess_Prompt.txt` 文件内容

### Requirement: 数学题目两阶段处理
系统 SHALL 实现数学题目的两阶段处理流程

#### Scenario: 处理套路知识类题目
- **WHEN** 第一个AI返回的分类结果为"套路知识类"
- **THEN** 直接保留预处理内容，存入结果集

#### Scenario: 处理思维提升类题目
- **WHEN** 第一个AI返回的分类结果为"思维提升类"
- **THEN** 调用第二个AI提示词进行深度拆解，将结果存入结果集

### Requirement: 按题目ID处理并保存
系统 SHALL 支持按指定题目ID进行处理并保存结果

#### Scenario: 处理单个题目
- **WHEN** 调用 `process_math_question(data_dir, question_id)`
- **THEN** 加载题目 → 两阶段处理 → 将结果保存到原JSON的 `math_processing_result` 字段

#### Scenario: 批量处理题目
- **WHEN** 调用 `batch_process_math_questions(data_dir, question_ids)`
- **THEN** 多线程处理所有题目并保存结果

### Requirement: 结果数据结构
系统 SHALL 定义标准的处理结果数据结构

#### Scenario: 结果格式
- **WHEN** 处理完成
- **THEN** 结果包含 `unit_content`、`classify_result`、`pre_process` 字段，存储在JSON的 `math_processing_result` 数组中

## MODIFIED Requirements
无（纯新增功能）

## REMOVED Requirements
无
