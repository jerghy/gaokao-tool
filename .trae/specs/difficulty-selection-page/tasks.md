# Tasks

- [x] Task 1: 添加后端 API 端点
  - [x] SubTask 1.1: 在 app.py 中添加 `GET /api/questions-with-difficulties` 端点，筛选并返回包含难点的题目列表
  - [x] SubTask 1.2: 在 app.py 中添加 `PUT /api/questions/<id>/selected-difficulties` 端点，保存选择的难点ID
  - [x] SubTask 1.3: 添加 `/difficulty` 路由，返回 difficulty.html 页面

- [x] Task 2: 创建难点选择页面
  - [x] SubTask 2.1: 创建 `static/difficulty.html` 文件
  - [x] SubTask 2.2: 实现左侧题目列表区域（显示包含难点的题目）
  - [x] SubTask 2.3: 实现右侧难点卡片展示区域
  - [x] SubTask 2.4: 实现难点卡片组件（显示难点名称、等级、考点、适配分数段、突破价值，右侧多选框）
  - [x] SubTask 2.5: 实现保存按钮和保存逻辑
  - [x] SubTask 2.6: 实现加载已选择难点的逻辑

# Task Dependencies
- Task 2 依赖 Task 1（需要后端 API 支持）
