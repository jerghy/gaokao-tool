# AI 工作流增强 Spec

## Why
当前 AI 系统虽然已经原子化了基础功能，但编写 AI 工作流时仍存在以下痛点：

1. **参数传递繁琐** - 每次调用都需要手动传入 `data_dir`、`api_key`、`model` 等重复参数
2. **数据流不连贯** - 搜索返回 ID 列表 → 需要手动循环获取每个题目的完整数据 → 再提取文本和图片 → 最后调用 AI
3. **结果保存分散** - 处理完成后需要单独调用保存函数
4. **缺少上下文对象** - 没有一个统一的对象来持有 `data_dir`、配置等上下文信息

目标是实现「搜索 → 获取 → 处理 → 保存」全链路的流畅体验。

## What Changes
- 新增 `AIContext` 上下文管理类，自动持有 `data_dir`、配置等公共参数
- 新增 `Question` 数据对象，封装题目数据并提供便捷方法
- 增强现有函数，支持链式调用和隐式上下文
- 新增工作流快捷函数

## Impact
- Affected code: `ai/base.py`, 新增 `ai/workflow.py`
- 向后兼容：所有现有 API 保持不变

## ADDED Requirements

### Requirement: AIContext 上下文管理
系统 SHALL 提供 `AIContext` 类用于管理工作流中的共享状态（data_dir、API 配置等）

#### Scenario: 创建上下文并使用
- **WHEN** 用户创建 `AIContext(data_dir="data")`
- **THEN** 上下文自动持有 data_dir、默认 AIConfig，后续操作可省略这些参数

### Requirement: Question 数据对象
系统 SHALL 提供 `Question` 类封装单个题目的完整数据

#### Scenario: 从 ID 获取 Question 对象
- **WHEN** 用户调用 `Question.load("20260328150917", ctx)` 或 `ctx.question("20260328150917")`
- **THEN** 返回包含 question_text、answer_text、image_paths、sub_questions 等属性的对象

#### Scenario: Question 对象直接调用 AI
- **WHEN** 用户对 Question 对象调用 `.ai(prompt)` 或 `.process(prompt, output_field)`
- **THEN** 自动使用题目的文本、图片调用 AI 并可选保存结果

#### Scenario: Question 对象链式访问子问题
- **WHEN** 用户调用 `question.sub_questions` 或 `question.filter_sub(tags=["思维"])`
- **THEN** 返回过滤后的子问题列表，每个子问题也是 Question 对象

### Requirement: 搜索结果直接获取 Question 列表
系统 SHALL 支持从搜索结果直接获取 Question 对象列表

#### Scenario: 搜索并获取题目列表
- **WHEN** 用户调用 `ctx.search("tag:数学")` 或 `ctx.search_questions("tag:数学")`
- **THEN** 返回 `list[Question]` 对象列表，可直接遍历处理

### Requirement: 批量处理快捷方式
系统 SHALL 提供批量处理的便捷方法

#### Scenario: 对搜索结果批量调用 AI
- **WHEN** 用户对 Question 列表调用 `.batch_ai(prompt, output_field)`
- **THEN** 自动多线程处理所有题目并保存结果

### Requirement: 工作流示例代码风格
最终目标代码风格如下：

```python
from ai import AIContext

# 创建上下文（只需设置一次）
ctx = AIContext(data_dir="data")

# 方式1：搜索 + 批量处理（一行搞定）
results = ctx.search("tag:数学").batch_ai(MATH_PROMPT, "math_thinking_chain")

# 方式2：逐个处理 + 自定义逻辑
for q in ctx.search("tag:化学"):
    result = q.ai(ANALYSIS_PROMPT)
    expansion = q.ai(EXPAND_PROMPT, context=result)  # 上一步结果作为上下文
    q.save("my_workflow_result", result=expansion)

# 方式3：处理子问题
q = ctx.question("20260328150917")
for sub in q.subs(tags=["思维"]):
    sub.ai(THINKING_PROMPT, "sub_thinking")
```

## MODIFIED Requirements
无（纯新增功能）
