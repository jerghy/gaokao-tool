# Tasks

- [x] Task 1: 实现提示词加载功能
  - [x] SubTask 1.1: 创建 `load_math_prompt(prompt_name)` 函数，从 `ai/tsc/` 目录加载txt文件
  - [x] SubTask 1.2: 定义两个常量 `MATH_SPLIT_CLASSIFY_PROMPT` 和 `MATH_THINKING_CHAIN_PROMPT`

- [x] Task 2: 实现数据结构定义
  - [x] SubTask 2.1: 创建 `MathUnit` dataclass，包含 `unit_content`、`classify_result`、`pre_process` 字段
  - [x] SubTask 2.2: 创建 `MathProcessResult` dataclass，包含题目ID和处理结果列表

- [x] Task 3: 实现第一阶段处理（拆分分类预处理）
  - [x] SubTask 3.1: 创建 `split_and_classify()` 函数，调用第一个AI提示词
  - [x] SubTask 3.2: 实现JSON解析和校验逻辑

- [x] Task 4: 实现第二阶段处理（思维提升类深度拆解）
  - [x] SubTask 4.1: 创建 `deep_parse_thinking()` 函数，调用第二个AI提示词
  - [x] SubTask 4.2: 实现分支处理逻辑：套路知识类直接保留，思维提升类深度处理

- [x] Task 5: 实现主处理流程
  - [x] SubTask 5.1: 创建 `process_math_question()` 函数，整合两阶段处理
  - [x] SubTask 5.2: 实现结果保存到原JSON文件的 `math_processing_result` 字段

- [x] Task 6: 实现批量处理功能
  - [x] SubTask 6.1: 创建 `batch_process_math_questions()` 函数，支持多线程处理
  - [x] SubTask 6.2: 实现进度显示和错误处理

# Task Dependencies
- [Task 3] depends on [Task 1, Task 2]
- [Task 4] depends on [Task 1, Task 2]
- [Task 5] depends on [Task 3, Task 4]
- [Task 6] depends on [Task 5]
