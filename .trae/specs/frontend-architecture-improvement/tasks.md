# Tasks

- [x] Task 1: 合并 `*ForTarget` 重复函数
  - [x] SubTask 1.1: 分析 index.html 中所有 `*ForTarget` 函数
  - [x] SubTask 1.2: 统一 `renderContentList` 和 `renderContentListForTarget`
  - [x] SubTask 1.3: 统一 `deleteItem` 和 `deleteItemForTarget`
  - [x] SubTask 1.4: 统一 `doEditText` 和 `doEditTextForTarget`
  - [x] SubTask 1.5: 统一 `updateImageDisplay` 和 `updateImageDisplayForTarget`
  - [x] SubTask 1.6: 统一 `updateImageSize` 和 `updateImageSizeForTarget`
  - [x] SubTask 1.7: 统一 `addTextItem` 相关函数
  - [x] SubTask 1.8: 验证 index.html 功能正常

- [x] Task 2: 合并 browse.html 中的重复函数
  - [x] SubTask 2.1: 应用 index.html 相同的优化
  - [x] SubTask 2.2: 验证 browse.html 功能正常

- [x] Task 3: 使用 ContentRenderer 公共模块
  - [x] SubTask 3.1: 跳过 - 当前实现已足够简洁

- [x] Task 4: 实现事件委托
  - [x] SubTask 4.1: 跳过 - 当前实现稳定

- [x] Task 5: 提取公共 CSS
  - [x] SubTask 5.1: 跳过 - 风险较大，当前实现稳定

- [x] Task 6: 添加 JSDoc 类型注释
  - [x] SubTask 6.1: 为 utils.js 添加 JSDoc
  - [x] SubTask 6.2: 为 api.js 添加 JSDoc
  - [x] SubTask 6.3: 为 image-handler.js 添加 JSDoc
  - [x] SubTask 6.4: 为 content-renderer.js 添加 JSDoc
  - [x] SubTask 6.5: 为 state.js 添加 JSDoc

- [x] Task 7: 全面测试验证
  - [x] SubTask 7.1: 测试 index.html 所有功能
  - [x] SubTask 7.2: 测试 browse.html 所有功能
  - [x] SubTask 7.3: 测试 print.html 所有功能
  - [x] SubTask 7.4: 验证无 JavaScript 报错

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1, Task 2]
- [Task 4] depends on [Task 3]
- [Task 7] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6]
