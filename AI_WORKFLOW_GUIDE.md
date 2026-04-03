# AI 工作流开发指南

本文档详细介绍如何使用 AI 工作流系统编写 AI 处理流程。通过本指南，你将学会如何利用原子化的功能模块快速构建复杂的 AI 工作流。

## 目录

- [系统架构概述](#系统架构概述)
- [快速开始](#快速开始)
- [核心组件详解](#核心组件详解)
  - [AIContext 上下文管理](#aicontext-上下文管理)
  - [Question 数据对象](#question-数据对象)
  - [batch_ai 批量处理](#batch_ai-批量处理)
- [基础工具函数](#基础工具函数)
  - [ReasoningEffort 推理深度枚举](#reasoningeffort-推理深度枚举)
  - [AIConfig 配置类](#aiconfig-配置类)
  - [AIClient 客户端类](#aiclient-客户端类)
- [使用场景示例](#使用场景示例)
- [最佳实践](#最佳实践)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 系统架构概述

### 分层设计

AI 工作流系统采用三层架构设计，从底层到高层依次为：

```
┌─────────────────────────────────────────────────────────┐
│                    workflow.py                          │
│              高层工作流 API（AIContext、Question）         │
├─────────────────────────────────────────────────────────┤
│                generic_processor.py                      │
│           中层处理器（搜索、批量处理、结果保存）             │
├─────────────────────────────────────────────────────────┤
│                      base.py                            │
│        底层原子化功能（配置、客户端、图片处理、API调用）      │
└─────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 职责 | 主要导出 |
|------|------|----------|
| `base.py` | 底层原子化功能 | `AIConfig`, `AIClient`, `call_ai_api`, `build_input_content` |
| `generic_processor.py` | 中层处理逻辑 | `search_questions_via_api`, `process_with_generic_ai`, `batch_process_generic` |
| `workflow.py` | 高层工作流 API | `AIContext`, `Question`, `batch_ai` |

### 数据流向

```
搜索请求 → API 服务 → 题目 ID 列表
                ↓
         加载题目 JSON 文件
                ↓
         解析文本和图片路径
                ↓
         构建 AI 输入内容
                ↓
         调用豆包大模型 API
                ↓
         提取响应文本
                ↓
         保存结果到 JSON 文件
```

### 与火山引擎豆包大模型的集成

系统使用火山引擎豆包大模型（`doubao-seed-2-0-pro-260215`）作为默认 AI 模型，通过 `volcenginesdkarkruntime` SDK 进行调用：

- **API 端点**: `https://ark.cn-beijing.volces.com/api/v3`
- **调用方式**: `responses.create` API
- **支持特性**: 
  - 多模态输入（文本 + 图片）
  - 推理深度控制（`reasoning_effort`）
  - 输出长度控制（`max_output_tokens`）

---

## 快速开始

### 环境准备

1. **安装依赖**:
```bash
pip install volcenginesdkarkruntime requests
```

2. **配置 API Key**:
```bash
# 设置环境变量
export ARK_API_KEY="your-api-key-here"
```

### 最简示例

```python
from ai import AIContext

# 创建上下文
ctx = AIContext(data_dir="data")

# 搜索并批量处理
results = ctx.search("tag:数学")
for q in results:
    result = q.ai("请分析这道题目的解题思路")
    print(f"题目 {q.id}: {result[:100]}...")
```

### 完整工作流示例

```python
from ai import AIContext, batch_ai

# 定义提示词
MATH_THINKING_PROMPT = """你是一位数学教育专家。请分析以下数学题目，输出详细的思维链分析。

要求：
1. 识别题目类型和考查的知识点
2. 分析解题思路和关键步骤
3. 指出可能的易错点
4. 给出学习建议

请以 JSON 格式输出结果。"""

# 创建上下文
ctx = AIContext(data_dir="data")

# 方式一：批量处理（推荐）
questions = ctx.search("tag:数学")
results = batch_ai(questions, MATH_THINKING_PROMPT, "math_thinking_chain", max_workers=3)

# 方式二：逐个处理（适合需要自定义逻辑的场景）
for q in ctx.search("tag:物理"):
    result = q.ai(MATH_THINKING_PROMPT, output_field="physics_analysis")
    print(f"处理完成: {q.id}")
```

---

## 核心组件详解

### AIContext 上下文管理

`AIContext` 是工作流的核心上下文管理器，负责持有共享状态和提供便捷方法。

#### 创建上下文

```python
from ai import AIContext

# 基本创建
ctx = AIContext(data_dir="data")

# 完整配置
ctx = AIContext(
    data_dir="data",                    # 数据目录路径
    api_key="your-api-key",             # API Key（可选，默认从环境变量读取）
    model="doubao-seed-2-0-pro-260215", # 模型名称
    api_base_url="http://localhost:5000" # API 服务地址
)
```

#### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data_dir` | `str` | 必填 | 题目 JSON 文件存储目录 |
| `api_key` | `str` | 环境变量 `ARK_API_KEY` | 火山引擎 API Key |
| `model` | `str` | `doubao-seed-2-0-pro-260215` | AI 模型名称 |
| `api_base_url` | `str` | `http://localhost:5000` | 搜索 API 服务地址 |

#### 上下文方法

**获取单个题目**:
```python
# 通过 ID 获取 Question 对象
q = ctx.question("20260328150917")
```

**搜索题目**:
```python
# 搜索返回 Question 列表
questions = ctx.search("tag:数学")
questions = ctx.search_questions("tag:物理")  # 别名方法

# 支持的搜索语法
ctx.search("tag:数学")           # 按标签搜索
ctx.search("数学")               # 全文搜索
ctx.search("tag:数学 tag:高考")  # 多标签搜索
```

**访问配置**:
```python
# 获取当前配置
config = ctx.config
print(config.model)           # 模型名称
print(config.max_output_tokens)  # 最大输出长度
```

---

### Question 数据对象

`Question` 类封装单个题目的完整数据，提供便捷的数据访问和 AI 调用方法。

#### 对象属性

```python
q = ctx.question("20260328150917")

# 基本属性
q.id              # 题目 ID（str）
q.question_text   # 题目文本内容（str）
q.answer_text     # 答案文本内容（str）
q.image_paths     # 图片路径列表（list[str]）
q.sub_questions   # 子问题列表（list[Question]）
q.raw_data        # 原始 JSON 数据（dict）
```

#### 加载方式

```python
from ai import AIContext, Question

ctx = AIContext(data_dir="data")

# 方式一：通过上下文加载（推荐）
q = ctx.question("20260328150917")

# 方式二：直接加载
q = Question.load("20260328150917", ctx=ctx)
```

#### AI 调用方法

**基本调用**:
```python
# 调用 AI 并返回结果
result = q.ai("请分析这道题目")

# 调用 AI 并自动保存结果
result = q.ai("请分析这道题目", output_field="analysis_result")
```

**带额外上下文**:
```python
# 上一步结果作为下一步输入
analysis = q.ai("请分析这道题目")
expansion = q.ai("请根据分析结果扩展知识点", context=analysis)
```

**自定义参数**:
```python
from ai import ReasoningEffort

result = q.ai(
    "请分析这道题目",
    output_field="deep_analysis",
    max_output_tokens=65536,    # 自定义输出长度
    reasoning_effort=ReasoningEffort.high,  # 推理深度（推荐使用枚举）
    # reasoning_effort="high"   # 字符串方式也支持
    model="doubao-seed-2-0-pro-260215"  # 自定义模型
)
```

**ai() 方法参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `system_prompt` | `str` | 必填 | 系统提示词 |
| `output_field` | `str` | `None` | 保存结果的字段名，为空则不保存 |
| `context` | `str` | `None` | 额外的上下文信息 |
| `max_output_tokens` | `int` | `131072` | 最大输出 token 数 |
| `reasoning_effort` | `ReasoningEffort \| str` | `ReasoningEffort.high` | 推理深度（推荐使用枚举） |
| `model` | `str` | 上下文配置 | 自定义模型 |

#### 结果保存

```python
# 方式一：ai() 调用时自动保存
q.ai("分析题目", output_field="analysis")

# 方式二：手动保存
result = q.ai("分析题目")
q.save("analysis", result=result)

# 方式三：保存最后一次结果
result = q.ai("分析题目")
q.save("analysis")  # 自动使用最后一次结果
```

#### 子问题操作

```python
# 获取所有子问题
subs = q.subs
subs = q.sub_questions  # 别名

# 按标签过滤子问题
thinking_subs = q.filter_sub(tags=["思维"])
calc_subs = q.filter_sub(tags=["计算", "证明"], require_all=False)  # 满足任一标签
both_subs = q.filter_sub(tags=["思维", "计算"], require_all=True)   # 满足所有标签

# 处理子问题
for sub in q.filter_sub(tags=["思维"]):
    sub.ai("分析这道思维题的解题思路", output_field="sub_analysis")
```

---

### batch_ai 批量处理

`batch_ai` 函数提供多线程批量处理能力，自动处理进度显示和结果统计。

#### 基本用法

```python
from ai import AIContext, batch_ai

ctx = AIContext(data_dir="data")
questions = ctx.search("tag:数学")

# 批量处理
results = batch_ai(
    questions,
    system_prompt="请分析这道数学题",
    output_field="math_analysis"
)
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `questions` | `list[Question]` | 必填 | 要处理的题目列表 |
| `system_prompt` | `str` | 必填 | 系统提示词 |
| `output_field` | `str` | `None` | 保存结果的字段名 |
| `max_workers` | `int` | `3` | 并发线程数 |
| `max_output_tokens` | `int` | `131072` | 最大输出 token 数 |
| `reasoning_effort` | `ReasoningEffort \| str` | `ReasoningEffort.high` | 推理深度 |
| `skip_if_exists` | `bool` | `True` | 跳过已处理项 |

#### 返回结果

```python
results = batch_ai(questions, prompt, "field")

# 结果结构
{
    "success": ["id1", "id2", ...],      # 成功的题目 ID
    "failed": [                          # 失败的题目
        {"id": "id3", "reason": "错误信息"},
        ...
    ],
    "skipped": ["id4", ...]              # 跳过的题目 ID
}
```

#### 控制台输出示例

```
共 50 个题目需要处理
输出字段: math_analysis
并发数: 3
============================================================
[1/50] ✓ 20260328150917: 处理完成
[2/50] ~ 20260328150918: 已存在，跳过
[3/50] ✗ 20260328150919: API 请求超时
...
============================================================
处理完成: 成功 45 个, 失败 2 个, 跳过 3 个

失败列表:
  - 20260328150919: API 请求超时
  - 20260328150925: 网络连接失败
```

---

## 基础工具函数

### ReasoningEffort 推理深度枚举

`ReasoningEffort` 是推理深度的枚举类，用于避免字符串拼写错误：

```python
from ai import ReasoningEffort

# 四个级别
ReasoningEffort.minimal  # 最小推理，快速响应
ReasoningEffort.low      # 低推理深度
ReasoningEffort.medium   # 中等推理深度
ReasoningEffort.high     # 深度推理（默认）
```

**使用示例**:
```python
from ai import AIContext, ReasoningEffort

ctx = AIContext(data_dir="data")
q = ctx.question("20260328150917")

# 使用枚举（推荐）
result = q.ai("分析题目", reasoning_effort=ReasoningEffort.high)

# 字符串方式也支持（不推荐，容易拼写错误）
result = q.ai("分析题目", reasoning_effort="high")
```

### AIConfig 配置类

`AIConfig` 是 AI 调用的配置数据类：

```python
from ai.base import AIConfig, ReasoningEffort

# 默认配置
config = AIConfig()

# 自定义配置
config = AIConfig(
    api_key="your-api-key",
    model="doubao-seed-2-0-pro-260215",
    max_output_tokens=131072,
    reasoning_effort=ReasoningEffort.high,  # 推荐使用枚举
    timeout=1800,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)
```

**配置参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | `str` | 环境变量 | API 密钥 |
| `model` | `str` | `doubao-seed-2-0-pro-260215` | 模型名称 |
| `max_output_tokens` | `int` | `131072` | 最大输出 token |
| `reasoning_effort` | `ReasoningEffort \| str` | `ReasoningEffort.high` | 推理深度 |
| `timeout` | `int` | `1800` | 请求超时（秒） |
| `base_url` | `str` | 火山引擎地址 | API 基础 URL |

### AIClient 客户端类

`AIClient` 是单例模式的 AI 客户端：

```python
from ai.base import AIClient, AIConfig

# 使用默认配置
client = AIClient()

# 使用自定义配置
config = AIConfig(api_key="your-key", model="doubao-seed-2-0-pro-260215")
client = AIClient(config)

# 调用 AI
result = client.call(
    system_prompt="你是一个助手",
    user_content=[{"type": "input_text", "text": "你好"}]
)
```

### 图片处理函数

**编码图片为 Base64**:
```python
from ai.base import encode_image_to_base64

base64_str = encode_image_to_base64("/path/to/image.png")
```

**获取图片 MIME 类型**:
```python
from ai.base import get_image_media_type

media_type = get_image_media_type("/path/to/image.jpg")  # "image/jpeg"
media_type = get_image_media_type("/path/to/image.png")  # "image/png"
```

### 内容构建函数

**构建 AI 输入内容**:
```python
from ai.base import build_input_content

# 纯文本
content = build_input_content(text="这是题目内容")

# 文本 + 图片
content = build_input_content(
    text="请分析这道题",
    image_paths=["/path/to/image1.png", "/path/to/image2.jpg"]
)

# 返回格式
# [
#     {"type": "input_image", "image_url": "data:image/png;base64,..."},
#     {"type": "input_text", "text": "请分析这道题"}
# ]
```

**解析 items 文本**:
```python
from ai.base import parse_items_text

items = [
    {"type": "text", "content": "题目内容"},
    {"type": "image", "config_id": "xxx"},
    {"type": "richtext", "content": "<b>加粗</b>"}
]
text = parse_items_text(items)  # "题目内容<b>加粗</b>"
```

### API 调用函数

**直接调用 AI API**:
```python
from ai.base import call_ai_api

result = call_ai_api(
    system_prompt="你是一个数学老师",
    user_text="请解释什么是勾股定理",
    user_image_paths=["/path/to/theorem.png"],
    max_output_tokens=65536,
    reasoning_effort="high"
)
```

**提取响应文本**:
```python
from ai.base import extract_response_text

# 从 response 对象提取文本
text = extract_response_text(response)
```

### 图片路径解析

**加载 images.json 数据**:
```python
from ai.base import load_images_data

images_data = load_images_data("data")
# 返回: {"images": {...}, "configs": {...}}
```

**通过 config_id 获取图片路径**:
```python
from ai.base import get_image_path_by_config_id

path = get_image_path_by_config_id("config_123", "data")
# 返回: "/full/path/to/image.png" 或 None
```

**从 items 提取图片路径**:
```python
from ai.base import extract_image_paths_from_items

items = [
    {"type": "image", "config_id": "config_123"},
    {"type": "image", "src": "images/photo.jpg"}
]
paths = extract_image_paths_from_items(items, "data")
# 返回: ["/full/path/to/image1.png", "/full/path/to/photo.jpg"]
```

---

## 使用场景示例

### 基础使用

#### 创建上下文并处理单个题目

```python
from ai import AIContext

# 创建上下文
ctx = AIContext(data_dir="data")

# 获取题目
q = ctx.question("20260328150917")

# 调用 AI
result = q.ai("请分析这道题目的解题思路")

# 保存结果
q.save("analysis", result)
```

#### 搜索并批量处理

```python
from ai import AIContext, batch_ai

ctx = AIContext(data_dir="data")

# 搜索题目
questions = ctx.search("tag:数学")

# 批量处理
results = batch_ai(
    questions,
    system_prompt="请分析这道数学题的解题思路",
    output_field="math_analysis",
    max_workers=5
)

print(f"成功: {len(results['success'])} 个")
print(f"失败: {len(results['failed'])} 个")
```

### 高级用法

#### 链式处理

```python
from ai import AIContext

ctx = AIContext(data_dir="data")

for q in ctx.search("tag:物理"):
    # 第一步：分析题目
    analysis = q.ai("请分析这道物理题的考点和解题思路")
    
    # 第二步：基于分析生成练习
    practice = q.ai(
        "请根据分析结果，生成 3 道类似的练习题",
        context=analysis
    )
    
    # 第三步：保存所有结果
    q.save("physics_analysis", analysis)
    q.save("practice_questions", practice)
```

#### 子问题过滤处理

```python
from ai import AIContext

ctx = AIContext(data_dir="data")

# 获取有子问题的题目
q = ctx.question("20260328150917")

# 只处理"思维"类型的子问题
for sub in q.filter_sub(tags=["思维"]):
    result = sub.ai(
        "请分析这道思维题的培养目标和解题策略",
        output_field="thinking_analysis"
    )
    print(f"子问题 {sub.id}: 处理完成")

# 处理同时包含"计算"和"证明"标签的子问题
for sub in q.filter_sub(tags=["计算", "证明"], require_all=True):
    sub.ai("请分析这道综合题", output_field="comprehensive_analysis")
```

#### 自定义配置

```python
from ai import AIContext, AIConfig

# 使用自定义模型配置
ctx = AIContext(
    data_dir="data",
    model="doubao-seed-2-0-pro-260215",
    api_key="your-custom-api-key"
)

# 单次调用使用不同参数
q = ctx.question("20260328150917")
result = q.ai(
    "请深入分析这道题",
    max_output_tokens=262144,    # 更长的输出
    reasoning_effort="high",      # 深度推理
    model="doubao-seed-2-0-pro-260215"
)
```

### 实战案例

#### 案例一：数学思维链分析

```python
from ai import AIContext, batch_ai

MATH_THINKING_PROMPT = """你是一位资深的数学教育专家。请对以下数学题目进行深度思维链分析。

请按以下结构输出 JSON 格式的分析结果：

```json
{
    "topic": "题目主题",
    "difficulty": "难度等级（1-5）",
    "knowledge_points": ["知识点1", "知识点2"],
    "thinking_chain": [
        {
            "step": 1,
            "description": "理解题意",
            "guidance": "引导学生理解题目的指导语"
        }
    ],
    "common_mistakes": ["常见错误1", "常见错误2"],
    "extension": "拓展思考方向"
}
```

请确保输出是有效的 JSON 格式。"""

ctx = AIContext(data_dir="data")

# 批量处理数学题
questions = ctx.search("tag:数学")
results = batch_ai(
    questions,
    MATH_THINKING_PROMPT,
    output_field="math_thinking_chain",
    max_workers=3
)

# 处理失败的题目
for failed in results["failed"]:
    print(f"需要重试: {failed['id']} - {failed['reason']}")
```

#### 案例二：错题归因分析

```python
from ai import AIContext

ERROR_ANALYSIS_PROMPT = """你是一位教育诊断专家。请分析学生的错误答案，找出错误原因。

请输出 JSON 格式：
```json
{
    "error_type": "概念错误/计算错误/理解错误/方法错误",
    "error_description": "错误的具体描述",
    "root_cause": "根本原因分析",
    "remediation": "补救措施建议",
    "similar_problems": "建议练习的类似题目类型"
}
```"""

ctx = AIContext(data_dir="data")

# 处理标记为"错题"的题目
for q in ctx.search("tag:错题"):
    # 检查是否有学生答案
    student_answer = q.raw_data.get("student_answer", "")
    if not student_answer:
        continue
    
    # 添加学生答案作为上下文
    result = q.ai(
        ERROR_ANALYSIS_PROMPT,
        context=f"学生答案：{student_answer}",
        output_field="error_analysis"
    )
```

#### 案例三：知识点提取与标签生成

```python
from ai import AIContext, batch_ai

KNOWLEDGE_EXTRACTION_PROMPT = """请分析以下题目，提取相关知识点并生成标签。

输出 JSON 格式：
```json
{
    "subject": "学科",
    "topics": ["主题1", "主题2"],
    "knowledge_points": ["知识点1", "知识点2"],
    "skills": ["技能1", "技能2"],
    "suggested_tags": ["标签1", "标签2"],
    "difficulty_level": "基础/中等/困难"
}
```"""

ctx = AIContext(data_dir="data")

# 批量处理
questions = ctx.search("")  # 空搜索获取所有题目
results = batch_ai(
    questions,
    KNOWLEDGE_EXTRACTION_PROMPT,
    output_field="knowledge_metadata",
    max_workers=5
)

# 统计结果
import json
from collections import Counter

all_tags = []
for q in questions:
    metadata = q.raw_data.get("knowledge_metadata")
    if metadata:
        try:
            data = json.loads(metadata) if isinstance(metadata, str) else metadata
            all_tags.extend(data.get("suggested_tags", []))
        except:
            pass

print("标签统计:")
for tag, count in Counter(all_tags).most_common(20):
    print(f"  {tag}: {count}")
```

---

## 最佳实践

### 性能优化

#### 并发数设置

```python
# 推荐：根据 API 限制设置并发数
# 火山引擎默认 QPS 限制，建议 3-5 个并发
results = batch_ai(questions, prompt, "field", max_workers=3)

# 高吞吐场景：使用更大的并发（需确认 API 限制）
results = batch_ai(questions, prompt, "field", max_workers=10)
```

#### 跳过已处理项

```python
# 默认行为：自动跳过已有结果的题目
results = batch_ai(questions, prompt, "field")  # skip_if_exists=True

# 强制重新处理
results = batch_ai(questions, prompt, "field", skip_if_exists=False)
```

#### 分批处理大量数据

```python
from ai import AIContext, batch_ai

ctx = AIContext(data_dir="data")
all_questions = ctx.search("tag:数学")

# 分批处理，每批 100 个
batch_size = 100
for i in range(0, len(all_questions), batch_size):
    batch = all_questions[i:i+batch_size]
    print(f"处理第 {i//batch_size + 1} 批...")
    results = batch_ai(batch, prompt, "field", max_workers=3)
```

### 错误处理

#### 常见错误类型

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| `ValueError: API KEY未配置` | 未设置 API Key | 设置 `ARK_API_KEY` 环境变量或传入 `api_key` |
| `FileNotFoundError` | 题目文件不存在 | 检查 `data_dir` 和题目 ID |
| `requests.RequestException` | 网络请求失败 | 检查网络连接和 API 地址 |
| `TimeoutError` | 请求超时 | 增加 `timeout` 配置或减少输出长度 |

#### 错误处理模式

```python
from ai import AIContext

ctx = AIContext(data_dir="data")

failed_questions = []

for q in ctx.search("tag:数学"):
    try:
        result = q.ai("分析题目", output_field="analysis")
    except Exception as e:
        print(f"处理失败 {q.id}: {e}")
        failed_questions.append(q.id)
        continue

# 重试失败的题目
for qid in failed_questions:
    try:
        q = ctx.question(qid)
        result = q.ai("分析题目", output_field="analysis")
        print(f"重试成功: {qid}")
    except Exception as e:
        print(f"重试失败: {qid} - {e}")
```

### 提示词编写

#### 结构化提示词

```python
GOOD_PROMPT = """你是一位专业的数学教师。请分析以下数学题目。

## 任务要求
1. 识别题目类型
2. 分析解题思路
3. 指出易错点

## 输出格式
请以 JSON 格式输出：
```json
{
    "type": "题目类型",
    "solution": "解题思路",
    "mistakes": ["易错点"]
}
```

## 注意事项
- 保持输出格式正确
- 分析要具体详细"""
```

#### 多模态输入处理

```python
# 系统自动处理图片，提示词中无需特殊说明
result = q.ai("""请分析这道几何题：

1. 识别图形类型
2. 分析已知条件
3. 给出证明思路

图片已自动包含在输入中，请直接分析。""")
```

---

## API 参考

### ai.workflow 模块

#### ReasoningEffort

```python
from enum import Enum

class ReasoningEffort(Enum):
    minimal = "minimal"  # 最小推理
    low = "low"          # 低推理深度
    medium = "medium"    # 中等推理深度
    high = "high"        # 深度推理（默认）
```

#### AIContext

```python
class AIContext:
    def __init__(
        self,
        data_dir: str,
        api_key: Optional[str] = None,
        model: str = "doubao-seed-2-0-pro-260215",
        api_base_url: str = "http://localhost:5000"
    ): ...
    
    @property
    def config(self) -> AIConfig: ...
    
    def question(self, question_id: str) -> Question: ...
    def search(self, query: str) -> list[Question]: ...
    def search_questions(self, query: str) -> list[Question]: ...
```

#### Question

```python
class Question:
    def __init__(
        self,
        id: str,
        question_text: str = "",
        answer_text: str = "",
        image_paths: Optional[list[str]] = None,
        sub_questions: Optional[list["Question"]] = None,
        raw_data: Optional[dict] = None,
        _ctx: Optional[AIContext] = None,
    ): ...
    
    @staticmethod
    def load(question_id: str, ctx: AIContext) -> "Question": ...
    
    def ai(
        self,
        system_prompt: str,
        output_field: Optional[str] = None,
        context: Optional[str] = None,
        max_output_tokens: int = 131072,
        reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> str: ...
    
    def process(
        self,
        system_prompt: str,
        output_field: str,
        tags: Optional[list[str]] = None,
        require_all: bool = False,
        **kwargs
    ) -> list: ...
    
    def save(self, field: str, result: Any = None) -> None: ...
    
    @property
    def subs(self) -> list["Question"]: ...
    
    def filter_sub(
        self,
        tags: Optional[list[str]] = None,
        require_all: bool = False
    ) -> list["Question"]: ...
```

#### batch_ai

```python
def batch_ai(
    questions: list[Question],
    system_prompt: str,
    output_field: str = None,
    max_workers: int = 3,
    max_output_tokens: int = 131072,
    reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high,
    skip_if_exists: bool = True,
    **kwargs
) -> dict: ...
```

### ai.base 模块

#### ReasoningEffort

```python
class ReasoningEffort(Enum):
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
```

#### AIConfig

```python
@dataclass
class AIConfig:
    api_key: str = field(default_factory=lambda: os.getenv("ARK_API_KEY", ""))
    model: str = "doubao-seed-2-0-pro-260215"
    max_output_tokens: int = 131072
    reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high
    timeout: int = 1800
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
```

#### AIClient

```python
class AIClient:
    def __new__(cls, config: Optional[AIConfig] = None): ...
    def __init__(self, config: Optional[AIConfig] = None): ...
    
    @property
    def client(self) -> Ark: ...
    @property
    def config(self) -> AIConfig: ...
    
    def call(
        self,
        system_prompt: str,
        user_content: list[dict],
        model: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
    ) -> str: ...
```

#### 工具函数

```python
def encode_image_to_base64(image_path: str) -> str: ...
def get_image_media_type(image_path: str) -> str: ...
def extract_response_text(response) -> str: ...
def build_input_content(text: str = "", image_paths: list[str] = None) -> list[dict]: ...
def parse_items_text(items: list) -> str: ...
def call_ai_api(...) -> str: ...
def load_images_data(data_dir: str) -> dict: ...
def get_image_path_by_config_id(config_id: str, data_dir: str, images_data: Optional[dict] = None) -> Optional[str]: ...
def extract_image_paths_from_items(items: list, data_dir: str, images_data: Optional[dict] = None) -> list[str]: ...
```

### ai.generic_processor 模块

```python
def search_questions_via_api(
    search_query: str,
    api_base_url: str = "http://localhost:5000",
    page_size: int = 1000,
) -> list[str]: ...

def get_question_via_api(
    question_id: str,
    api_base_url: str = "http://localhost:5000",
) -> Optional[dict]: ...

def process_with_generic_ai(
    data_dir: str,
    question_id: str,
    system_prompt: str,
    output_field: str = "generic_ai_result",
    ...
) -> list[GenericAIResult]: ...

def batch_process_generic(
    data_dir: str,
    system_prompt: str,
    search_query: str = "",
    ...
) -> dict: ...

def batch_process_generic_by_ids(
    data_dir: str,
    question_ids: list[str],
    system_prompt: str,
    ...
) -> dict: ...
```

---

## 常见问题

### Q: 如何设置 API Key？

**A:** 有三种方式：

```python
# 方式一：环境变量（推荐）
export ARK_API_KEY="your-api-key"

# 方式二：创建上下文时传入
ctx = AIContext(data_dir="data", api_key="your-api-key")

# 方式三：调用时传入
q.ai("prompt", api_key="your-api-key")
```

### Q: 如何处理包含图片的题目？

**A:** 系统自动处理图片，无需额外操作：

```python
q = ctx.question("20260328150917")
# q.image_paths 已自动解析
result = q.ai("请分析这道题")  # 图片自动包含在输入中
```

### Q: 如何跳过已处理的题目？

**A:** `batch_ai` 默认跳过已有结果的题目：

```python
# 默认行为
batch_ai(questions, prompt, "field")  # 自动跳过

# 强制重新处理
batch_ai(questions, prompt, "field", skip_if_exists=False)
```

### Q: 如何调试 AI 调用？

**A:** 可以使用底层 API 进行调试：

```python
from ai.base import call_ai_api, build_input_content

# 直接调用 API
result = call_ai_api(
    system_prompt="测试提示词",
    user_text="测试内容",
    user_image_paths=["/path/to/image.png"]
)
print(result)
```

### Q: 如何处理超时问题？

**A:** 增加 timeout 配置：

```python
from ai.base import AIConfig, AIClient

config = AIConfig(timeout=3600)  # 1 小时超时
client = AIClient(config)
```

### Q: 如何使用不同的模型？

**A:** 在创建上下文或调用时指定：

```python
# 全局设置
ctx = AIContext(data_dir="data", model="other-model")

# 单次调用
q.ai("prompt", model="other-model")
```

---

## 总结

本指南涵盖了 AI 工作流系统的核心概念和使用方法。通过 `AIContext`、`Question` 和 `batch_ai` 等高层 API，你可以快速构建复杂的 AI 处理流程。

**推荐学习路径**：
1. 从[快速开始](#快速开始)入手，运行基本示例
2. 学习[核心组件详解](#核心组件详解)，理解工作流设计
3. 参考[使用场景示例](#使用场景示例)，实现具体需求
4. 查阅[API 参考](#api-参考)，了解完整功能

**下一步**：
- 尝试编写自己的提示词
- 构建多阶段工作流
- 优化并发和错误处理策略
