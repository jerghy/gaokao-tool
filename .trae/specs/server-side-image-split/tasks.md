# Tasks

- [x] Task 1: 后端实现图片分割 API
  - [x] SubTask 1.1: 添加 `/api/split-image` POST 接口
  - [x] SubTask 1.2: 使用 PIL/Pillow 裁剪图片
  - [x] SubTask 1.3: 分割后的图片保存到 `split_cache` 目录
  - [x] SubTask 1.4: 实现缓存机制，相同参数直接返回缓存结果
  - [x] SubTask 1.5: 返回分割后的图片 URL 列表

- [x] Task 2: 前端打印页面改为请求服务端分割
  - [x] SubTask 2.1: 移除前端 Canvas 裁剪代码
  - [x] SubTask 2.2: 添加请求服务端分割 API 的函数
  - [x] SubTask 2.3: 修改渲染函数使用服务端返回的图片 URL

- [x] Task 3: 添加清理过期缓存机制
  - [x] SubTask 3.1: 添加定时清理过期分割图片的功能

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
