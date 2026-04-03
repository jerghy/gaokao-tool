# AI 工作流高级功能 Spec

## Why
当前 AI 工作流系统提供了基础的原子化函数，但在实际复杂应用场景中，还需要更多高级功能：
- 流式输出提升用户体验
- 结果缓存节省 API 成本
- 任务队列支持大批量处理
- 进度持久化支持中断恢复
- 结果验证确保输出质量

## What Changes
- 添加流式输出支持 (`call_ai_stream`)
- 添加结果缓存机制 (`CachedAI`)
- 添加任务队列 (`TaskQueue`)
- 添加进度持久化 (`ProgressTracker`)
- 添加结果验证 (`validate_result`)
- 添加速率限制 (`RateLimiter`)
- 添加结果转换 (`parse_json_result`, `extract_markdown_code`)

## Impact
- Affected specs: ai-workflow-enhancement
- Affected code: `ai/base.py`, `ai/queue.py`, `ai/cache.py`

## ADDED Requirements

### Requirement: 流式输出
系统应支持流式输出，实时返回 AI 响应。

#### Scenario: 流式文本输出
- **WHEN** 用户调用 `call_ai_stream`
- **THEN** 系统通过回调函数实时返回文本片段

```python
def on_chunk(chunk: str):
    print(chunk, end='', flush=True)

result = call_ai_stream(ai, "系统提示", "用户输入", on_chunk=on_chunk)
```

### Requirement: 结果缓存
系统应支持缓存 AI 调用结果，避免重复调用。

#### Scenario: 缓存命中
- **WHEN** 相同输入再次调用
- **THEN** 直接返回缓存结果，不调用 API

```python
cached_ai = CachedAI(ai, cache_dir=".ai_cache")
result1 = cached_ai.call("系统提示", "用户输入")  # 调用 API
result2 = cached_ai.call("系统提示", "用户输入")  # 使用缓存
```

### Requirement: 任务队列
系统应支持任务队列管理大批量任务。

#### Scenario: 任务队列处理
- **WHEN** 用户添加大量任务到队列
- **THEN** 系统按并发限制逐步处理，支持暂停/恢复

```python
queue = TaskQueue(ai, max_workers=3)
queue.add_tasks(tasks)
queue.start()
# 程序中断后
queue.load_progress()
queue.resume()
```

### Requirement: 进度持久化
系统应支持保存和恢复处理进度。

#### Scenario: 进度恢复
- **WHEN** 程序中断后重新启动
- **THEN** 可以从上次进度继续处理

```python
tracker = ProgressTracker("progress.json")
tracker.mark_done("task_1")
tracker.mark_done("task_2")
# 中断后
tracker.load()
remaining = tracker.get_pending(all_tasks)
```

### Requirement: 速率限制
系统应支持 API 调用速率限制。

#### Scenario: 速率控制
- **WHEN** 设置每分钟最大请求数
- **THEN** 系统自动控制调用频率

```python
limiter = RateLimiter(max_requests=60, per_seconds=60)
limiter.wait_if_needed()
result = call_ai(...)
```

### Requirement: 结果验证
系统应支持验证 AI 输出格式。

#### Scenario: JSON 验证
- **WHEN** 期望 JSON 格式输出
- **THEN** 自动验证并解析

```python
result = call_ai_text(ai, "输出JSON格式", "问题")
data = validate_result(result, expect_json=True)
```

### Requirement: 结果转换
系统应提供常用的结果转换函数。

#### Scenario: 提取代码块
- **WHEN** AI 输出包含代码块
- **THEN** 提取指定语言的代码

```python
result = "```python\nprint('hello')\n```"
code = extract_markdown_code(result, language="python")
```

## MODIFIED Requirements
无

## REMOVED Requirements
无
