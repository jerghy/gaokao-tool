# AI 模块系统性优化 Spec

## Why
当前 AI 模块经过多轮迭代已具备完整功能，但存在严重的代码重复和架构不一致问题：
1. **批量处理代码大量重复** — 8个处理器各自实现了几乎相同的 ThreadPoolExecutor 批量处理逻辑（约60-80行/个），总计500+行重复代码
2. **数据加载路径不统一** — `loader.ProcessedQuestion`、`workflow.Question`、各处理器内部各自加载数据，3套并行体系
3. **模块职责不清** — `base.py` 承载了AI调用、图片处理、内容构建、数据加载4类职责，450行代码；`__init__.py` 导出100+符号
4. **搜索功能重复** — `thinking_processor.py` 内部自建了 `search_questions()`，与 `search_engine.py` 和 `AIContext.search()` 功能完全重叠
5. **日志不规范** — 全部使用 `print()` 而非 `logging`，无法控制输出级别
6. **处理器与工作流层脱节** — `workflow.py` 提供了 `AIContext`/`Question`/`batch_ai`，但各处理器完全不用，自行实现批量逻辑

## What Changes
- 提取通用批量处理框架 `ai/batch.py`，消除8个处理器中的重复代码
- 统一数据加载，让所有处理器通过 `Question` 对象获取数据，废弃 `ProcessedQuestion`
- 拆分 `base.py` 为 `ai/ai_client.py`（AI调用）+ `ai/content.py`（内容构建）+ `ai/images.py`（图片处理）
- 清理 `__init__.py`，只导出核心公共API（约30个符号）
- 删除 `thinking_processor.py` 中的 `search_questions()` 及相关函数，统一使用 `AIContext.search()`
- 全局替换 `print()` 为 `logging`
- 重构各处理器，使其成为薄层：定义提示词 + 定义结果类型 + 实现单条处理逻辑，批量处理由框架承担

## Impact
- Affected specs: ai-workflow-enhancement, ai-workflow-advanced-features, code-refactor-ai-prompts
- Affected code: `ai/base.py`, `ai/__init__.py`, `ai/loader.py`, `ai/workflow.py`, `ai/generic_processor.py`, `ai/thinking_processor.py`, `ai/immersion_processor.py`, `ai/chemistry_processor.py`, `ai/chemistry_difficulty_processor.py`, `ai/tag_processor.py`, `ai/math_processor.py`, `ai/evaluator.py`, `ai/preprocessor.py`, `ai/image_annotator.py`
- **BREAKING**: `ProcessedQuestion` 废弃，改用 `Question`；`thinking_processor.search_questions()` 删除；`base.py` 中的函数迁移到新模块（旧路径通过 `base.py` 重导出保持兼容）

## ADDED Requirements

### Requirement: 通用批量处理框架
系统 SHALL 在 `ai/batch.py` 中提供通用批量处理框架，替代各处理器中重复的 ThreadPoolExecutor 代码。

#### Scenario: 使用框架进行批量处理
- **WHEN** 处理器调用 `run_batch(process_fn, items, max_workers=3, skip_fn=None)`
- **THEN** 框架自动处理并发执行、进度打印、结果聚合（success/failed/skipped）、错误捕获

#### Scenario: 自定义跳过逻辑
- **WHEN** 处理器提供 `skip_fn(item) -> bool`
- **THEN** 框架在处理前检查是否跳过，跳过的项目计入 skipped

#### Scenario: 进度输出使用 logging
- **WHEN** 批量处理执行中
- **THEN** 进度信息通过 `logging.info` 输出，而非 `print()`

### Requirement: 统一数据加载
系统 SHALL 以 `workflow.Question` 作为唯一的数据加载入口，废弃 `loader.ProcessedQuestion`。

#### Scenario: 处理器通过 Question 获取数据
- **WHEN** 处理器需要获取题目文本和图片
- **THEN** 通过 `Question` 对象的 `question_text`、`answer_text`、`image_paths` 属性获取

#### Scenario: ProcessedQuestion 兼容过渡
- **WHEN** 外部代码仍导入 `ProcessedQuestion`
- **THEN** `loader.py` 中保留 `ProcessedQuestion` 定义但标记为 deprecated，内部实现委托给 `Question`

### Requirement: base.py 拆分为专注模块
系统 SHALL 将 `base.py` 拆分为3个职责单一的模块。

#### Scenario: AI调用相关
- **WHEN** 代码需要调用AI API
- **THEN** 从 `ai/ai_client.py` 导入 `AI`, `Model`, `ReasoningEffort`, `call_ai`, `call_ai_text`, `call_ai_json`, `call_ai_with_images`, `call_ai_with_retry`, `call_ai_batch`, `call_ai_stream`, `BatchResult`, `call_ai_batch_texts`, `call_ai_batch_texts_safe`, `parallel_map`, `parallel_map_safe`

#### Scenario: 内容构建相关
- **WHEN** 代码需要构建AI输入内容或解析文本
- **THEN** 从 `ai/content.py` 导入 `build_input_content`, `parse_items_text`

#### Scenario: 图片处理相关
- **WHEN** 代码需要处理图片编码或路径解析
- **THEN** 从 `ai/images.py` 导入 `encode_image_to_base64`, `get_image_media_type`, `load_images_data`, `get_image_path_by_config_id`, `extract_image_paths_from_items`

#### Scenario: base.py 兼容重导出
- **WHEN** 外部代码从 `ai.base` 导入函数
- **THEN** `base.py` 通过重导出保持兼容，不破坏现有导入路径

### Requirement: 清理 __init__.py 公共API
系统 SHALL 将 `__init__.py` 的导出精简为核心公共API。

#### Scenario: 核心API导出
- **WHEN** 用户 `from ai import ...`
- **THEN** 可用的核心符号包括：`AI`, `Model`, `ReasoningEffort`, `AIContext`, `Question`, `batch_ai`, `call_ai`, `call_ai_text`, `call_ai_json`, `call_ai_with_images`, `call_ai_with_retry`, `call_ai_stream`, `CachedAI`, `ProgressTracker`, `RateLimiter`, `BatchResult`, `build_input_content`, `parse_items_text`, `encode_image_to_base64`, `validate_result`, `parse_json_result`, `extract_markdown_code`, `parallel_map`, `parallel_map_safe`
- **AND** 各处理器的专用类/函数仍可通过 `from ai.xxx_processor import ...` 导入

### Requirement: 删除重复搜索实现
系统 SHALL 删除 `thinking_processor.py` 中的 `search_questions()`、`tokenize_search_query()`、`match_tag()`、`match_text()`、`get_effective_tags()` 函数。

#### Scenario: 搜索统一走 AIContext
- **WHEN** 需要搜索题目
- **THEN** 使用 `AIContext.search()` 或 `search_engine.SearchEngine`，不再使用 `thinking_processor.search_questions()`

#### Scenario: immersion_processor 不再依赖 thinking_processor 的搜索
- **WHEN** `immersion_processor.py` 需要搜索题目
- **THEN** 通过 `AIContext.search()` 或直接传入题目ID列表

### Requirement: 全局 logging 替换 print
系统 SHALL 将所有 AI 模块中的 `print()` 替换为 `logging`。

#### Scenario: 批量处理进度输出
- **WHEN** 批量处理执行
- **THEN** 进度信息通过 `logger.info()` 输出

#### Scenario: 错误信息输出
- **WHEN** 处理过程中发生错误
- **THEN** 错误信息通过 `logger.warning()` 或 `logger.error()` 输出

### Requirement: 处理器薄层重构
系统 SHALL 将各处理器重构为薄层，批量处理逻辑委托给通用框架。

#### Scenario: 处理器结构
- **WHEN** 实现一个新的处理器
- **THEN** 只需定义：1) 提示词函数 2) 结果 dataclass 3) 单条处理函数 `process_one(question, **kwargs) -> Result`
- **AND** 批量处理由 `run_batch(process_one, questions, ...)` 承担

#### Scenario: 现有处理器重构
- **WHEN** 重构 `chemistry_processor.py` 等现有处理器
- **THEN** 保留其公共API不变（函数签名和返回类型），内部实现改为使用通用框架

## MODIFIED Requirements

### Requirement: AIContext 搜索能力增强
原 `AIContext.search()` 依赖 `generic_processor.search_questions_via_api()` 通过HTTP请求搜索。现增加本地搜索模式，当 Flask 服务未运行时可直接从文件系统搜索。

#### Scenario: 本地搜索模式
- **WHEN** `AIContext` 初始化时传入 `api_base_url=None` 或调用 `search_local()`
- **THEN** 直接从 `data_dir` 读取文件进行搜索，无需 Flask 服务

### Requirement: Question 类增强
`Question` 类增加便捷方法，使其能完全替代 `ProcessedQuestion` 和各处理器内部的数据加载。

#### Scenario: 从 raw_data 中获取标签
- **WHEN** 调用 `question.tags`
- **THEN** 返回题目的标签列表（包括子问题标签）

#### Scenario: 获取子问题文本
- **WHEN** 调用 `question.sub_question_texts`
- **THEN** 返回所有子问题的文本内容列表

## REMOVED Requirements

### Requirement: thinking_processor.search_questions() 及相关函数
**Reason**: 与 `search_engine.py` 和 `AIContext.search()` 功能完全重叠，且实现更简陋（不支持布尔搜索、AST解析）
**Migration**: 使用 `AIContext.search(query)` 或 `from ai.generic_processor import search_questions_via_api`

### Requirement: loader.ProcessedQuestion 作为主数据对象
**Reason**: 与 `workflow.Question` 功能重叠，且 `Question` 提供更丰富的方法（ai调用、保存、子问题过滤等）
**Migration**: 使用 `Question.load(id, ctx)` 或 `ctx.question(id)`；`ProcessedQuestion` 保留定义但标记 deprecated
