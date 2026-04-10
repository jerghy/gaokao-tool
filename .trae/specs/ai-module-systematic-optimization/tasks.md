# Tasks

- [x] Task 1: 创建通用批量处理框架 `ai/batch.py`
  - [x] SubTask 1.1: 实现 `run_batch(process_fn, items, max_workers, skip_fn, desc)` 函数，封装 ThreadPoolExecutor、进度打印、结果聚合（success/failed/skipped）、错误捕获
  - [x] SubTask 1.2: 实现 `BatchProgress` dataclass 用于返回批量处理结果统计
  - [x] SubTask 1.3: 使用 `logging` 替代 `print` 输出进度
  - [x] SubTask 1.4: 验证框架行为

- [x] Task 2: 拆分 `base.py` 为三个专注模块
  - [x] SubTask 2.1: 创建 `ai/ai_client.py`，迁移 AI 调用相关
  - [x] SubTask 2.2: 创建 `ai/content.py`，迁移内容构建相关
  - [x] SubTask 2.3: 创建 `ai/images.py`，迁移图片处理相关
  - [x] SubTask 2.4: 将 `base.py` 改为重导出模块，保持向后兼容

- [x] Task 3: 增强 `Question` 类，使其完全替代 `ProcessedQuestion`
  - [x] SubTask 3.1: 在 `Question` 类中添加 `tags` 属性
  - [x] SubTask 3.2: 在 `Question` 类中添加 `sub_question_texts` 属性
  - [x] SubTask 3.3: 在 `loader.py` 中将 `ProcessedQuestion` 标记为 deprecated

- [x] Task 4: 删除 `thinking_processor.py` 中的重复搜索实现
  - [x] SubTask 4.1: 删除 `search_questions()`, `tokenize_search_query()`, `match_tag()`, `match_text()`, `get_effective_tags()` 函数
  - [x] SubTask 4.2: 修改 `extract_thinking_targets()` 内联标签提取逻辑
  - [x] SubTask 4.3: 修改 `immersion_processor.py` 中对 `thinking_processor.search_questions` 的依赖

- [x] Task 5: 增强 `AIContext` 本地搜索能力
  - [x] SubTask 5.1: 在 `AIContext` 中添加 `search_local(query)` 方法
  - [x] SubTask 5.2: 修改 `AIContext.search()` 逻辑：当 `api_base_url` 为 None 时自动使用本地搜索

- [x] Task 6: 重构各处理器使用通用批量框架
  - [x] SubTask 6.1: 重构 `generic_processor.py`
  - [x] SubTask 6.2: 重构 `thinking_processor.py`
  - [x] SubTask 6.3: 重构 `immersion_processor.py`
  - [x] SubTask 6.4: 重构 `chemistry_processor.py`
  - [x] SubTask 6.5: 重构 `chemistry_difficulty_processor.py`
  - [x] SubTask 6.6: 重构 `tag_processor.py`
  - [x] SubTask 6.7: 重构 `math_processor.py`
  - [x] SubTask 6.8: 重构 `workflow.py`（batch_ai）
  - [x] SubTask 6.9: `evaluator.py` 无批量处理代码，无需重构
  - [x] SubTask 6.10: 重构 `image_annotator.py`

- [x] Task 7: 全局 logging 替换 print
  - [x] SubTask 7.1: 在所有 AI 模块文件中添加 `logger = logging.getLogger(__name__)`
  - [x] SubTask 7.2: 将所有 `print()` 调用替换为对应的 `logger.info()`/`logger.warning()`
  - [x] SubTask 7.3: 删除各文件中的 `print_lock = threading.Lock()` 全局变量

- [x] Task 8: 清理 `__init__.py` 公共API
  - [x] SubTask 8.1: 精简 `__init__.py` 导出列表为核心公共API（26个符号）
  - [x] SubTask 8.2: 确保各处理器的专用类/函数仍可通过 `from ai.xxx import ...` 导入

- [x] Task 9: 验证与回归测试
  - [x] SubTask 9.1: 验证 `from ai.base import ...` 的向后兼容性
  - [x] SubTask 9.2: 验证 `from ai import ...` 核心API可用性
  - [x] SubTask 9.3: 验证所有处理器模块导入正常

# Task Dependencies
- [Task 2] depends on nothing (可独立开始)
- [Task 1] depends on nothing (可独立开始)
- [Task 3] depends on nothing (可独立开始)
- [Task 5] depends on [Task 4]
- [Task 4] depends on [Task 5]
- [Task 6] depends on [Task 1, Task 3]
- [Task 7] depends on [Task 6]
- [Task 8] depends on [Task 2]
- [Task 9] depends on [Task 6, Task 7, Task 8]

# Parallelizable Work
- Task 1, Task 2, Task 3 可并行执行
- Task 6 的各子任务可并行执行
