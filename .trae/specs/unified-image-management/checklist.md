# Checklist

## 后端实现
- [x] `image_manager.py` 模块实现完成，包含完整的 CRUD 操作
- [x] `images.json` 数据结构正确，包含 `images` 和 `configs` 字段
- [x] `/api/upload-image` 接口返回图片ID
- [x] `/api/save` 接口正确处理图片配置的创建和更新
- [x] `/api/questions` 接口正确展开图片信息
- [x] `/api/images` 接口返回所有图片列表
- [x] 图片使用追踪功能正常工作

## 前端实现
- [x] `index.html` 图片上传功能正常
- [x] `index.html` 图片保存功能正常，存储配置ID
- [x] `index.html` 字框标注功能正常
- [x] `index.html` 分割线功能正常
- [x] `browse.html` 图片显示功能正常
- [x] `browse.html` 图片编辑功能正常
- [x] `print.html` 图片打印功能正常
- [x] `print.html` 字框缩放功能正常
- [x] `print.html` 图片分割功能正常

## 数据迁移
- [x] 迁移脚本正确提取所有图片信息
- [x] `images.json` 文件创建成功
- [x] 所有题目JSON文件更新成功
- [x] 迁移后数据完整性验证通过
- [x] 原始数据备份完成

## 功能验证
- [x] 新建题目并上传图片功能正常
- [x] 编辑现有题目功能正常
- [x] 删除题目功能正常
- [x] 同一图片被多个题目引用时数据不重复
- [x] 搜索功能正常工作
- [x] 标签功能正常工作
