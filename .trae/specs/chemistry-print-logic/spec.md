# 化学题目打印逻辑优化 Spec

## Why
当前打印系统对化学题目的打印格式不够优化，需要针对"化学"标签的题目加载 `chemistry_preprocessing` 和 `difficulty_teaching` 中的 AI 生成内容，提供更有针对性的训练材料打印格式。

## What Changes
- 新增化学题目特殊打印逻辑判断（基于"化学"标签）
- 新增 `chemistry_preprocessing.Accumulation` 内容渲染函数
- 新增 `difficulty_teaching` 内容渲染函数（Markdown格式）
- 在渲染 `difficulty_teaching` 前，根据 `selected_difficulty_ids` 从 `Difficulties` 中获取对应的 `DifficultyName` 作为标题
- 修改 `renderPreview()` 函数以支持化学题目的特殊渲染

## Impact
- Affected specs: 打印预览系统
- Affected code: `static/print.html` 中的渲染逻辑

## ADDED Requirements

### Requirement: 化学题目特殊打印格式

系统 SHALL 对标签包含"化学"的题目采用特殊的打印格式。

#### Scenario: 化学题目打印
- **WHEN** 用户选择打印标签包含"化学"的题目
- **THEN** 系统加载 `chemistry_preprocessing` 和 `difficulty_teaching` 内容并按指定格式渲染

### Requirement: Accumulation 内容渲染格式

系统 SHALL 对 `chemistry_preprocessing.Accumulation` 数组中的每个项目按以下格式渲染：

#### 渲染字段
1. **ExerciseType**：显示为题型标签（如"判断题"、"填空题"）
2. **ExamTag**：显示为考点标签
3. **AdaptScore**：显示为适配分数段
4. **ExerciseContent**：显示为题目内容
5. **AnswerAnalysis**：显示为答案解析

#### Scenario: Accumulation 渲染
- **WHEN** 题目包含 `chemistry_preprocessing.Accumulation` 数据
- **THEN** 按顺序渲染每个积累项，包含题型、考点、适配分数、题目内容和答案解析

### Requirement: Difficulty Teaching 渲染格式

系统 SHALL 对 `difficulty_teaching` 内容按以下格式渲染：

#### 渲染逻辑
1. 根据 `selected_difficulty_ids` 数组确定需要渲染的难点
2. 从 `chemistry_preprocessing.Difficulties` 中根据 `DifficultyID` 获取对应的 `DifficultyName`
3. 将 `DifficultyName` 作为标题显示在对应 `difficulty_teaching` 内容之前
4. 将 `difficulty_teaching` 中的 Markdown 内容渲染为 HTML

#### Scenario: Difficulty Teaching 渲染
- **WHEN** 题目包含 `difficulty_teaching` 数据
- **THEN** 根据 selected_difficulty_ids 渲染对应的难点教学内容，包含难点名称标题和 Markdown 内容

## MODIFIED Requirements

### Requirement: 打印预览渲染

原有的 `renderPreview()` 函数 SHALL 增加对化学题目的判断和特殊渲染逻辑。

#### Scenario: 化学题目识别
- **WHEN** 题目的 `tags` 数组包含"化学"
- **THEN** 调用化学题目专用渲染函数

#### Scenario: 题目渲染顺序
- **WHEN** 渲染化学题目
- **THEN** 按以下顺序渲染：题目内容 → Accumulation → Difficulty Teaching
