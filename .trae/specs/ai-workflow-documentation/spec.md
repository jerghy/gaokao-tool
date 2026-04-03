# AI 工作流文档 Spec

## Why
当前 AI 工作流系统已经实现了原子化功能模块和便捷的工作流 API，但缺乏面向开发者的详细使用文档。开发者需要一份完整的指南来了解如何使用这套系统编写 AI 工作流，包括核心概念、API 用法、实战示例和最佳实践。

## What Changes
- 创建 `AI_WORKFLOW_GUIDE.md` 文档
- 包含系统架构概述
- 包含核心组件详解（AIContext、Question、batch_ai）
- 包含基础工具函数说明
- 包含多种使用场景的代码示例
- 包含最佳实践和注意事项
- 包含完整 API 参考

## Impact
- Affected specs: 无（纯文档新增）
- Affected code: 无

## ADDED Requirements

### Requirement: 系统架构概述
文档应清晰说明 AI 工作流系统的整体架构和设计理念。

#### Scenario: 架构理解
- **WHEN** 开发者阅读文档
- **THEN** 能够了解：
  - 系统的分层设计（base → generic_processor → workflow）
  - 各模块的职责划分
  - 数据流向
  - 与火山引擎豆包大模型的集成方式

### Requirement: 核心组件详解
文档应详细说明每个核心组件的设计和用法。

#### Scenario: AIContext 上下文管理
- **WHEN** 开发者需要管理工作流上下文
- **THEN** 文档提供：
  - AIContext 的创建方式
  - 配置参数说明（data_dir、api_key、model、api_base_url）
  - 上下文方法（question、search、search_questions）

#### Scenario: Question 数据对象
- **WHEN** 开发者需要操作题目数据
- **THEN** 文档提供：
  - Question 对象的属性（id、question_text、answer_text、image_paths、sub_questions）
  - 加载方式（Question.load、ctx.question）
  - AI 调用方法（ai、process）
  - 结果保存方法（save）
  - 子问题操作（subs、filter_sub）

#### Scenario: 批量处理函数
- **WHEN** 开发者需要批量处理题目
- **THEN** 文档提供：
  - batch_ai 函数的参数和用法
  - 并发控制
  - 结果统计

### Requirement: 基础工具函数说明
文档应说明 base.py 中的基础工具函数。

#### Scenario: 工具函数使用
- **WHEN** 开发者需要使用底层功能
- **THEN** 文档提供：
  - AIConfig 配置类
  - AIClient 客户端类
  - 图片处理函数（encode_image_to_base64、get_image_media_type）
  - 内容构建函数（build_input_content、parse_items_text）
  - API 调用函数（call_ai_api、extract_response_text）

### Requirement: 使用场景示例
文档应提供多种实际使用场景的完整代码示例。

#### Scenario: 基础使用
- **WHEN** 开发者需要快速上手
- **THEN** 文档提供：
  - 创建上下文的基本示例
  - 单个题目处理示例
  - 搜索并批量处理示例

#### Scenario: 高级用法
- **WHEN** 开发者需要复杂工作流
- **THEN** 文档提供：
  - 链式处理示例（上一步结果作为下一步输入）
  - 子问题过滤处理示例
  - 自定义配置示例
  - 多阶段工作流示例

#### Scenario: 实战案例
- **WHEN** 开发者需要参考实际应用
- **THEN** 文档提供：
  - 数学思维链分析工作流
  - 错题归因分析工作流
  - 知识点提取工作流

### Requirement: 最佳实践
文档应提供使用 AI 工作流的最佳实践建议。

#### Scenario: 性能优化
- **WHEN** 开发者需要优化性能
- **THEN** 文档提供：
  - 并发数设置建议
  - 跳过已处理项的策略
  - 批量处理技巧

#### Scenario: 错误处理
- **WHEN** 开发者需要处理异常
- **THEN** 文档提供：
  - 常见错误类型
  - 错误处理模式
  - 重试策略建议

#### Scenario: 提示词编写
- **WHEN** 开发者需要编写系统提示词
- **THEN** 文档提供：
  - 提示词结构建议
  - 输出格式控制
  - 多模态输入处理

### Requirement: API 参考
文档应提供完整的 API 参考手册。

#### Scenario: 快速查阅
- **WHEN** 开发者需要查阅 API
- **THEN** 文档提供：
  - 所有公开类和函数的签名
  - 参数类型和默认值
  - 返回值类型
  - 使用示例

## MODIFIED Requirements
无

## REMOVED Requirements
无
