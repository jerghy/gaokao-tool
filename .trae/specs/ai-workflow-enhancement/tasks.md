# Tasks

- [x] Task 1: 创建 `ai/workflow.py` - 实现 AIContext 上下文管理类
  - [x] 1.1: 实现 `AIContext` 类，持有 `data_dir`、`AIConfig`、`api_base_url`
  - [x] 1.2: 实现 `ctx.question(id)` 方法，返回 `Question` 对象
  - [x] 1.3: 实现 `ctx.search(query)` 方法，返回 `list[Question]`
  - [x] 1.4: 实现 `ctx.search_questions(query)` 作为别名

- [x] Task 2: 创建 `ai/workflow.py` - 实现 Question 数据对象
  - [x] 2.1: 实现 `Question` 类，封装题目数据（id, text, answer, image_paths, sub_questions, raw_data）
  - [x] 2.2: 实现 `Question.load(id, ctx)` 静态方法从 JSON 加载
  - [x] 2.3: 实现 `Question.ai(prompt, **kwargs)` 方法调用 AI 并返回结果字符串
  - [x] 2.4: 实现 `Question.process(prompt, output_field, **kwargs)` 方法调用 AI 并保存到 JSON
  - [x] 2.5: 实现 `Question.save(field, result)` 方法保存结果到 JSON
  - [x] 2.6: 实现 `Question.subs(tags=None)` 方法返回过滤后的子问题列表
  - [x] 2.7: 实现 `Question.filter_sub(tags, require_all)` 子问题过滤
  - [x] 2.8: 实现 `list[Question].batch_ai(prompt, output_field, **kwargs)` 批量处理扩展方法

- [x] Task 3: 更新 `ai/__init__.py` 导出新模块
  - [x] 3.1: 导出 `AIContext`、`Question`、`batch_ai`

- [x] Task 4: 编写使用示例并验证
  - [x] 4.1: 验证 AIContext 基本功能
  - [x] 4.2: 验证 Question 加载和属性访问
  - [ ] 4.3: 验证 Question.ai() 调用（需要 API Key）
  - [ ] 4.4: 验证搜索 + 批量处理链式调用（需要 API 服务）
  - [ ] 4.5: 验证子问题处理

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1], [Task 2]
- [Task 4] depends on [Task 1], [Task 2], [Task 3]
