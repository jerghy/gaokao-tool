# Tasks

- [x] Task 1: 在错题收录页面添加端口输入框和WebSocket服务端逻辑
  - [x] SubTask 1.1: 在页面底部添加端口号输入框和连接状态显示
  - [x] SubTask 1.2: 实现WebSocket服务端监听逻辑（接收图片数据）
  - [x] SubTask 1.3: 将接收的图片数据模拟粘贴行为，调用图片上传接口
  - [x] SubTask 1.4: 显示连接状态（已连接/未连接）

- [x] Task 2: 在PDF查看器页面添加截图功能
  - [x] SubTask 2.1: 添加截图覆盖层和选择框样式
  - [x] SubTask 2.2: 实现鼠标拖拽选择截图区域逻辑
  - [x] SubTask 2.3: 实现Canvas截取PDF页面指定区域
  - [x] SubTask 2.4: 添加右键菜单（发送截图选项）
  - [x] SubTask 2.5: 支持Escape键或点击取消选择区域

- [x] Task 3: 在PDF查看器页面添加端口输入框和WebSocket客户端逻辑
  - [x] SubTask 3.1: 在工具栏添加端口号输入框和连接按钮
  - [x] SubTask 3.2: 实现WebSocket客户端连接逻辑
  - [x] SubTask 3.3: 发送前验证连接状态
  - [x] SubTask 3.4: 发送截图Base64数据到服务端

- [x] Task 4: 集成测试和优化
  - [x] SubTask 4.1: 测试端口连接建立和断开
  - [x] SubTask 4.2: 测试截图区域选择和取消
  - [x] SubTask 4.3: 测试图片传输和接收
  - [x] SubTask 4.4: 测试图片在错题页面的正确显示

# Task Dependencies
- [Task 3] depends on [Task 1] (需要先有服务端才能测试客户端连接)
- [Task 4] depends on [Task 1, Task 2, Task 3]
