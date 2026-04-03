# Tasks

- [x] Task 1: 创建图片管理模块 `image_manager.py`
  - [x] SubTask 1.1: 设计 `images.json` 数据结构
  - [x] SubTask 1.2: 实现 `ImageManager` 类，包含图片和配置的 CRUD 操作
  - [x] SubTask 1.3: 实现图片使用追踪功能
  - [x] SubTask 1.4: 添加线程安全锁

- [x] Task 2: 修改后端 API 接口
  - [x] SubTask 2.1: 修改 `/api/upload-image` 接口，返回图片ID
  - [x] SubTask 2.2: 修改 `/api/save` 接口，处理图片配置创建和更新
  - [x] SubTask 2.3: 修改 `/api/questions` 接口，展开图片信息
  - [x] SubTask 2.4: 修改 `/api/questions/<id>` PUT 接口
  - [x] SubTask 2.5: 新增 `/api/images` 接口，获取所有图片列表
  - [x] SubTask 2.6: 新增 `/api/images/<config_id>` 接口，获取单个图片配置

- [x] Task 3: 修改前端录入页面 `static/index.html`
  - [x] SubTask 3.1: 修改图片上传逻辑，使用新的API响应格式
  - [x] SubTask 3.2: 修改图片保存逻辑，存储配置ID
  - [x] SubTask 3.3: 修改字框标注保存逻辑
  - [x] SubTask 3.4: 修改分割线保存逻辑

- [x] Task 4: 修改前端浏览页面 `static/browse.html`
  - [x] SubTask 4.1: 修改图片显示逻辑，适配新的数据格式
  - [x] SubTask 4.2: 确保图片编辑功能正常工作

- [x] Task 5: 修改前端打印页面 `static/print.html`
  - [x] SubTask 5.1: 修改图片加载逻辑
  - [x] SubTask 5.2: 确保字框缩放功能正常
  - [x] SubTask 5.3: 确保图片分割功能正常

- [x] Task 6: 实现数据迁移脚本
  - [x] SubTask 6.1: 创建迁移脚本 `migrate_images.py`
  - [x] SubTask 6.2: 遍历所有题目JSON，提取图片信息
  - [x] SubTask 6.3: 创建 `images.json` 文件
  - [x] SubTask 6.4: 更新所有题目JSON文件

- [x] Task 7: 测试和验证
  - [x] SubTask 7.1: 测试图片上传功能
  - [x] SubTask 7.2: 测试题目保存和读取功能
  - [x] SubTask 7.3: 测试字框标注功能
  - [x] SubTask 7.4: 测试图片分割功能
  - [x] SubTask 7.5: 验证数据迁移正确性

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 2]
- [Task 5] depends on [Task 2]
- [Task 6] depends on [Task 1, Task 2, Task 3, Task 4, Task 5]
- [Task 7] depends on [Task 6]
