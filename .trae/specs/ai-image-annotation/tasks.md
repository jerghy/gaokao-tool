# Tasks

- [x] Task 1: 创建图片标注模块 `ai/image_annotator.py`
  - [x] SubTask 1.1: 定义数据结构（CharBox, SplitLine, AnnotationResult）
  - [x] SubTask 1.2: 实现 charBox 标注提示词
  - [x] SubTask 1.3: 实现 splitLines 标注提示词
  - [x] SubTask 1.4: 实现单图标注函数

- [x] Task 2: 实现批处理功能
  - [x] SubTask 2.1: 实现扫描未标注配置的函数
  - [x] SubTask 2.2: 实现多线程批处理逻辑
  - [x] SubTask 2.3: 实现进度输出
  - [x] SubTask 2.4: 实现结果保存到 images.json

- [x] Task 3: 创建命令行入口脚本
  - [x] SubTask 3.1: 创建 `annotate_images.py` 脚本
  - [x] SubTask 3.2: 添加命令行参数（并发数、跳过已标注等）
  - [x] SubTask 3.3: 添加帮助信息

- [x] Task 4: 更新 `ai/__init__.py` 导出
  - [x] SubTask 4.1: 导出新增的模块和函数

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 1]
