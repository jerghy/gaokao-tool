# Tasks

- [x] Task 1: 创建Python后端服务
  - [x] SubTask 1.1: 创建Flask应用主文件app.py
  - [x] SubTask 1.2: 实现静态文件服务路由
  - [x] SubTask 1.3: 实现图片上传保存接口（POST /api/upload-image）
  - [x] SubTask 1.4: 实现JSON保存接口（POST /api/save）
  - [x] SubTask 1.5: 创建img文件夹和data文件夹

- [x] Task 2: 创建前端HTML页面
  - [x] SubTask 2.1: 创建index.html基础结构
  - [x] SubTask 2.2: 实现左侧输入区域布局（包含原题/答案标签页）
  - [x] SubTask 2.3: 实现右侧A4预览区域布局（显示原题和答案）
  - [x] SubTask 2.4: 添加基础CSS样式

- [x] Task 3: 实现标签页切换功能
  - [x] SubTask 3.1: 创建原题和答案两个标签页
  - [x] SubTask 3.2: 实现标签页切换逻辑
  - [x] SubTask 3.3: 维护两个独立的内容列表

- [x] Task 4: 实现文本输入功能
  - [x] SubTask 4.1: 实现文本粘贴事件监听
  - [x] SubTask 4.2: 将文本添加到当前标签页的内容列表
  - [x] SubTask 4.3: 在预览区实时显示文本

- [x] Task 5: 实现图片输入功能
  - [x] SubTask 5.1: 实现图片粘贴事件监听
  - [x] SubTask 5.2: 调用后端API保存图片到img文件夹
  - [x] SubTask 5.3: 创建图片卡片组件（包含预览、显示方式选择、尺寸设置）
  - [x] SubTask 5.4: 实现图片删除功能

- [x] Task 6: 实现预览功能
  - [x] SubTask 6.1: 根据原题列表渲染原题预览
  - [x] SubTask 6.2: 根据答案列表渲染答案预览
  - [x] SubTask 6.3: 实现图片居中显示样式
  - [x] SubTask 6.4: 实现图片嵌入文字显示样式
  - [x] SubTask 6.5: 应用图片尺寸设置

- [x] Task 7: 实现JSON保存功能
  - [x] SubTask 7.1: 创建保存按钮
  - [x] SubTask 7.2: 收集原题和答案数据生成JSON
  - [x] SubTask 7.3: 调用后端API保存JSON文件到data文件夹
  - [x] SubTask 7.4: 保存成功后清空页面内容
  - [x] SubTask 7.5: 切换到原题标签页

# Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 2
- Task 4 依赖 Task 3
- Task 5 依赖 Task 1 和 Task 3
- Task 6 依赖 Task 4 和 Task 5
- Task 7 依赖 Task 6
