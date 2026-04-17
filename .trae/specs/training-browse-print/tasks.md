# Tasks

- [x] Task 1: 创建后端 API 接口
  - [x] SubTask 1.1: 在 app.py 中添加 `/api/training-items` 接口，返回所有训练题目
  - [x] SubTask 1.2: 在 app.py 中添加 `/api/training-ability-tags` 接口，返回能力点标签树

- [x] Task 2: 创建训练题目浏览页面 `static/training.html`
  - [x] SubTask 2.1: 创建页面基础结构（三栏布局）
  - [x] SubTask 2.2: 实现左侧能力点标签树组件
  - [x] SubTask 2.3: 实现中间训练题目列表组件（支持多选、分页）
  - [x] SubTask 2.4: 实现上方搜索框（复用 browse.html 的搜索逻辑）
  - [x] SubTask 2.5: 实现右侧训练题目详情展示
  - [x] SubTask 2.6: 实现右键菜单和批量打印跳转

- [x] Task 3: 创建训练题目打印页面 `static/training-print.html`
  - [x] SubTask 3.1: 创建打印页面基础结构
  - [x] SubTask 3.2: 实现训练题目打印卡片样式
  - [x] SubTask 3.3: 实现打印控制面板（布局、每页数量等）
  - [x] SubTask 3.4: 实现打印预览和打印功能

# Task Dependencies
- Task 2 依赖 Task 1（需要 API 接口）
- Task 3 依赖 Task 2（需要从浏览页面跳转）
