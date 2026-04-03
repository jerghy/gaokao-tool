# Tasks

- [x] Task 1: 创建文档框架和系统架构概述
  - [x] SubTask 1.1: 创建 AI_WORKFLOW_GUIDE.md 文件
  - [x] SubTask 1.2: 编写系统架构概述章节（分层设计、模块职责、数据流向）
  - [x] SubTask 1.3: 编写快速开始章节（安装、配置、最简示例）

- [x] Task 2: 编写核心组件详解
  - [x] SubTask 2.1: 编写 AIContext 上下文管理章节（创建、配置、方法）
  - [x] SubTask 2.2: 编写 Question 数据对象章节（属性、加载、AI调用、保存、子问题）
  - [x] SubTask 2.3: 编写 batch_ai 批量处理章节（参数、并发、结果）

- [x] Task 3: 编写基础工具函数说明
  - [x] SubTask 3.1: 编写 AIConfig 配置类说明
  - [x] SubTask 3.2: 编写 AIClient 客户端类说明
  - [x] SubTask 3.3: 编写图片处理函数说明
  - [x] SubTask 3.4: 编写内容构建和 API 调用函数说明

- [x] Task 4: 编写使用场景示例
  - [x] SubTask 4.1: 编写基础使用示例（创建上下文、单个处理、批量处理）
  - [x] SubTask 4.2: 编写高级用法示例（链式处理、子问题过滤、自定义配置）
  - [x] SubTask 4.3: 编写实战案例（数学思维链、错题归因、知识点提取）

- [x] Task 5: 编写最佳实践和 API 参考
  - [x] SubTask 5.1: 编写最佳实践章节（性能优化、错误处理、提示词编写）
  - [x] SubTask 5.2: 编写完整 API 参考手册
  - [x] SubTask 5.3: 编写常见问题 FAQ

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2]
- [Task 5] depends on [Task 2, Task 3, Task 4]
