# Tasks

- [x] Task 1: 创建后端配置模块 `config.py`
  - [x] SubTask 1.1: 提取所有路径常量到 Config 类
  - [x] SubTask 1.2: 提取文件路径常量到 Config 类
  - [x] SubTask 1.3: 在 app.py 中使用 Config 替换所有硬编码路径

- [x] Task 2: 创建数据访问层（Repository）
  - [x] SubTask 2.1: 创建 `repositories/question_repository.py`
  - [x] SubTask 2.2: 创建 `repositories/tag_repository.py`
  - [x] SubTask 2.3: 创建 `repositories/__init__.py`

- [x] Task 3: 创建服务层（Service）
  - [x] SubTask 3.1: 创建 `services/question_service.py`
  - [x] SubTask 3.2: 创建 `services/image_service.py`
  - [x] SubTask 3.3: 创建 `services/screenshot_service.py`
  - [x] SubTask 3.4: 创建 `services/__init__.py`

- [x] Task 4: 创建路由层（Blueprint）
  - [x] SubTask 4.1: 创建 `routes/question_routes.py`
  - [x] SubTask 4.2: 创建 `routes/image_routes.py`
  - [x] SubTask 4.3: 创建 `routes/screenshot_routes.py`
  - [x] SubTask 4.4: 创建 `routes/tag_routes.py`
  - [x] SubTask 4.5: 创建 `routes/page_routes.py`
  - [x] SubTask 4.6: 创建 `routes/__init__.py`

- [x] Task 5: 重构 app.py 为应用工厂
  - [x] SubTask 5.1: 创建 `create_app()` 工厂函数
  - [x] SubTask 5.2: 注册所有 Blueprint
  - [x] SubTask 5.3: 保留错误处理器注册
  - [x] SubTask 5.4: 保留静态文件服务路由
  - [x] SubTask 5.5: 确保 `if __name__ == '__main__'` 入口正常工作

- [x] Task 6: 前端 JS 模块提取 - browse.html
  - [x] SubTask 6.1: 创建 `static/js/browse.js`
  - [x] SubTask 6.2: 在 browse.html 中替换内联 JS
  - [x] SubTask 6.3: 验证浏览页面功能正常

- [x] Task 7: 前端 JS 模块提取 - index.html
  - [x] SubTask 7.1: 创建 `static/js/index.js`
  - [x] SubTask 7.2: 在 index.html 中替换内联 JS
  - [x] SubTask 7.3: 验证录入页面功能正常

- [x] Task 8: 前端 JS 模块提取 - print.html
  - [x] SubTask 8.1: 创建 `static/js/print.js`
  - [x] SubTask 8.2: 在 print.html 中替换内联 JS
  - [x] SubTask 8.3: 验证打印页面功能正常

- [x] Task 9: 前端公共 CSS 提取
  - [x] SubTask 9.1: 创建 `static/css/common.css`
  - [x] SubTask 9.2: 在各 HTML 页面中添加 common.css 引用
  - [x] SubTask 9.3: 从各页面删除已提取到 common.css 的重复 CSS
  - [x] SubTask 9.4: 验证所有页面样式正常

- [x] Task 10: 集成验证
  - [x] SubTask 10.1: 启动 Flask 应用，确认无启动错误
  - [x] SubTask 10.2: 测试所有 API 端点功能正常
  - [x] SubTask 10.3: 测试所有前端页面功能正常
  - [x] SubTask 10.4: 确认无 JavaScript 控制台错误

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 4]
- [Task 6, 7, 8, 9] 可并行执行，与后端重构无依赖
- [Task 10] depends on [Task 5, Task 6, Task 7, Task 8, Task 9]
