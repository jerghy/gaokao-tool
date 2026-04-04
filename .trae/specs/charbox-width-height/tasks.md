# Tasks

- [x] Task 1: 修改 CharBox 数据结构
  - [x] SubTask 1.1: 将 `size` 字段改为 `width` 和 `height`
  - [x] SubTask 1.2: 更新 `to_dict` 方法

- [x] Task 2: 修改 AI 解析逻辑
  - [x] SubTask 2.1: 修改 `_parse_charbox_response` 函数，直接计算 width 和 height

- [x] Task 3: 修改 browse.html
  - [x] SubTask 3.1: 修改 `drawCharBox` 函数，使用 width 和 height
  - [x] SubTask 3.2: 修改手动标注保存逻辑，保存 width 和 height

- [x] Task 4: 修改 print.html
  - [x] SubTask 4.1: 修改 `calculateImageScale` 函数，使用 max(width, height) 计算

- [x] Task 5: 运行 AI 重新生成所有标注
  - [x] SubTask 5.1: 执行 `python d:\space\html\print\annotate_images.py -i d:\space\html\print\images.json -w 8 --no-skip`

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1, Task 2, Task 3, Task 4]
