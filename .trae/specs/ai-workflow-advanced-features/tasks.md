# Tasks

- [x] Task 1: 添加流式输出支持
  - [x] SubTask 1.1: 实现 `call_ai_stream` 函数
  - [x] SubTask 1.2: 添加 `on_chunk` 回调参数
  - [x] SubTask 1.3: 更新 `__init__.py` 导出

- [x] Task 2: 添加结果缓存机制
  - [x] SubTask 2.1: 创建 `CachedAI` 类
  - [x] SubTask 2.2: 实现基于文件哈希的缓存 key
  - [x] SubTask 2.3: 支持缓存过期时间

- [x] Task 3: 添加进度持久化
  - [x] SubTask 3.1: 创建 `ProgressTracker` 类
  - [x] SubTask 3.2: 实现 `mark_done`, `get_pending` 方法
  - [x] SubTask 3.3: 支持 JSON 格式保存

- [x] Task 4: 添加速率限制
  - [x] SubTask 4.1: 创建 `RateLimiter` 类
  - [x] SubTask 4.2: 实现令牌桶算法
  - [x] SubTask 4.3: 添加 `wait_if_needed` 方法

- [x] Task 5: 添加结果验证和转换
  - [x] SubTask 5.1: 实现 `validate_result` 函数
  - [x] SubTask 5.2: 实现 `parse_json_result` 函数
  - [x] SubTask 5.3: 实现 `extract_markdown_code` 函数

- [ ] Task 6: 添加任务队列（可选）
  - [ ] SubTask 6.1: 创建 `TaskQueue` 类
  - [ ] SubTask 6.2: 实现暂停/恢复功能
  - [ ] SubTask 6.3: 集成进度持久化

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 6] depends on [Task 3, Task 4]
