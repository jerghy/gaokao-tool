# 数学题目打印逻辑优化 Spec

## Why
当前打印系统对数学题目的打印格式不够优化，需要针对"数学"标签的题目加载 `math_processing_result` 中的 AI 生成内容，提供更有针对性的训练材料打印格式。

## What Changes
- 新增数学题目特殊打印逻辑判断（基于"数学"标签）
- 新增 `math_processing_result` 内容渲染函数
- 新增"套路知识类"训练内容的格式化渲染
- 新增"思维提升类"内容的 Markdown 渲染
- 修改 `renderPreview()` 函数以支持数学题目的特殊渲染

## Impact
- Affected specs: 打印预览系统
- Affected code: `static/print.html` 中的渲染逻辑

## ADDED Requirements

### Requirement: 数学题目特殊打印格式

系统 SHALL 对标签包含"数学"的题目采用特殊的打印格式。

#### Scenario: 数学题目打印
- **WHEN** 用户选择打印标签包含"数学"的题目
- **THEN** 系统加载 `math_processing_result` 内容并按指定格式渲染

### Requirement: 套路知识类渲染格式

系统 SHALL 对 `classify_result` 为"套路知识类"的内容按以下格式渲染：

#### 训练类型格式
1. **套路反射训练**：
   - 显示问题（`question`）
   - 显示标准答案（`standard_answer`）
   - 不显示 `train_type` 字段

2. **知识易错训练**：
   - 显示训练形式标签（判断题/填空题）
   - 显示训练内容（`train_content`）
   - 显示答案（`answer`）
   - 不显示 `train_type` 和 `train_form` 字段名

#### Scenario: 套路知识类渲染
- **WHEN** `classify_result` 为"套路知识类"
- **THEN** 按训练类型分别渲染，隐藏字段名标签

### Requirement: 思维提升类渲染格式

系统 SHALL 对 `classify_result` 为"思维提升类"的内容按以下格式渲染：

#### 渲染内容
- 显示 `unit_content`（题目单元内容）
- 将 `pre_process` 作为 Markdown 格式渲染

#### Scenario: 思维提升类渲染
- **WHEN** `classify_result` 为"思维提升类"
- **THEN** 渲染 unit_content 和 Markdown 格式的 pre_process

## MODIFIED Requirements

### Requirement: 打印预览渲染

原有的 `renderPreview()` 函数 SHALL 增加对数学题目的判断和特殊渲染逻辑。

#### Scenario: 数学题目识别
- **WHEN** 题目的 `tags` 数组包含"数学"
- **THEN** 调用数学题目专用渲染函数
