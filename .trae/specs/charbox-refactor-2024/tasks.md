# Tasks

- [x] Task 1: 修改 AI 坐标解析逻辑
  - [x] SubTask 1.1: 修改 `_parse_charbox_response` 函数，将 AI 返回的坐标除以 1000 得到比例值
  - [x] SubTask 1.2: 确保坐标顺序正确（x1,y1 左上角，x2,y2 右下角）
  - [x] SubTask 1.3: 计算 size 为宽度和高度的最大值

- [x] Task 2: 修改 browse.html 字框显示逻辑
  - [x] SubTask 2.1: 确保 `drawCharBox` 函数正确使用比例坐标
  - [x] SubTask 2.2: 确保手动标注保存的格式与 AI 标注一致

- [x] Task 3: 修改 print.html 图片缩放逻辑
  - [x] SubTask 3.1: 确保 `calculateImageScale` 函数正确处理比例值
  - [x] SubTask 3.2: 移除像素值兼容逻辑（不再需要检测 size > 1）

- [x] Task 4: 运行 AI 重新生成所有标注
  - [x] SubTask 4.1: 执行 `python d:\space\html\print\annotate_images.py -i d:\space\html\print\images.json -w 8 --no-skip`

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1, Task 2, Task 3]
