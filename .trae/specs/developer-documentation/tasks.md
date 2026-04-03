# Tasks

- [x] Task 1: 创建开发者文档框架
  - [x] SubTask 1.1: 创建 `DEVELOPER.md` 文件
  - [x] SubTask 1.2: 编写文档目录结构
  - [x] SubTask 1.3: 编写技术栈说明

- [x] Task 2: 编写系统架构文档
  - [x] SubTask 2.1: 编写目录结构说明
  - [x] SubTask 2.2: 编写模块依赖关系图
  - [x] SubTask 2.3: 编写数据流向说明
  - [x] SubTask 2.4: 编写系统启动流程

- [x] Task 3: 编写核心模块文档
  - [x] SubTask 3.1: 编写 `app.py` 主应用文档
  - [x] SubTask 3.2: 编写 `image_manager.py` 图片管理模块文档
  - [x] SubTask 3.3: 编写 `tag_system.py` 标签系统文档
  - [x] SubTask 3.4: 编写 `search_engine.py` 搜索引擎文档
  - [x] SubTask 3.5: 编写 AI 模块文档（base.py, preprocessor.py 等）

- [x] Task 4: 编写数据结构规范
  - [x] SubTask 4.1: 编写题目JSON格式说明
  - [x] SubTask 4.2: 编写 images.json 格式说明
  - [x] SubTask 4.3: 编写 tags_data.json 格式说明
  - [x] SubTask 4.4: 编写 pending_screenshots.json 格式说明
  - [x] SubTask 4.5: 编写数据关系图

- [x] Task 5: 编写API接口规范
  - [x] SubTask 5.1: 编写题目相关API文档
  - [x] SubTask 5.2: 编写图片相关API文档
  - [x] SubTask 5.3: 编写标签相关API文档
  - [x] SubTask 5.4: 编写截图相关API文档
  - [x] SubTask 5.5: 编写搜索相关API文档

- [x] Task 6: 编写前端开发指南
  - [x] SubTask 6.1: 编写页面结构说明（index.html, browse.html, print.html）
  - [x] SubTask 6.2: 编写组件设计模式
  - [x] SubTask 6.3: 编写事件处理规范
  - [x] SubTask 6.4: 编写数据绑定方式说明

- [x] Task 7: 编写扩展开发指南
  - [x] SubTask 7.1: 编写添加新API的步骤
  - [x] SubTask 7.2: 编写添加新页面的步骤
  - [x] SubTask 7.3: 编写添加新AI处理器的步骤
  - [x] SubTask 7.4: 编写数据迁移注意事项

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1]
- [Task 6] depends on [Task 1]
- [Task 7] depends on [Task 2, Task 3, Task 4, Task 5, Task 6]
