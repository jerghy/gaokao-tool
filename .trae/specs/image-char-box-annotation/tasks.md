# Tasks

- [x] Task 1: 在 index.html 中添加字框标注界面和样式
  - [x] SubTask 1.1: 添加字框标注弹窗的 HTML 结构
  - [x] SubTask 1.2: 添加字框标注弹窗的 CSS 样式
  - [x] SubTask 1.3: 在图片卡片上添加"标注字框"按钮

- [x] Task 2: 实现字框标注绘制功能
  - [x] SubTask 2.1: 实现弹窗打开/关闭逻辑
  - [x] SubTask 2.2: 实现鼠标拖动绘制正方形的逻辑（强制等比例）
  - [x] SubTask 2.3: 实现字框的显示和更新
  - [x] SubTask 2.4: 实现字体大小选择（大/中/小）UI 和逻辑

- [x] Task 3: 实现字框数据存储
  - [x] SubTask 3.1: 将字框信息存储到图片 item 对象中
  - [x] SubTask 3.2: 在保存时包含字框数据
  - [x] SubTask 3.3: 在编辑时能加载已保存的字框数据

- [x] Task 4: 在 print.html 中实现图片缩放逻辑
  - [x] SubTask 4.1: 添加根据字框计算图片缩放比例的函数
  - [x] SubTask 4.2: 在渲染图片时应用缩放逻辑
  - [x] SubTask 4.3: 处理无字框标注的情况

- [x] Task 5: 在 browse.html 中支持字框显示和编辑
  - [x] SubTask 5.1: 在浏览页面显示字框标注按钮
  - [x] SubTask 5.2: 支持在浏览页面编辑字框

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 3]
