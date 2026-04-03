# Tasks

- [x] Task 1: 创建公共模块目录结构
  - [x] SubTask 1.1: 创建 `static/js/` 目录
  - [x] SubTask 1.2: 创建 `static/js/utils.js` 文件框架
  - [x] SubTask 1.3: 创建 `static/js/api.js` 文件框架
  - [x] SubTask 1.4: 创建 `static/js/image-handler.js` 文件框架
  - [x] SubTask 1.5: 创建 `static/js/content-renderer.js` 文件框架
  - [x] SubTask 1.6: 创建 `static/js/state.js` 文件框架

- [x] Task 2: 实现 utils.js 工具模块
  - [x] SubTask 2.1: 实现 `escapeHtml` 函数
  - [x] SubTask 2.2: 实现 `renderLatex` 函数
  - [x] SubTask 2.3: 实现 `processTextWithLatex` 函数
  - [x] SubTask 2.4: 实现 `renderRichtext` 函数
  - [x] SubTask 2.5: 实现 `cleanImageItem` 函数
  - [x] SubTask 2.6: 实现 `cleanItems` 函数

- [x] Task 3: 实现 api.js API封装模块
  - [x] SubTask 3.1: 实现 `api.uploadImage` 函数
  - [x] SubTask 3.2: 实现 `api.saveQuestion` 函数
  - [x] SubTask 3.3: 实现 `api.getQuestions` 函数
  - [x] SubTask 3.4: 实现 `api.updateQuestion` 函数
  - [x] SubTask 3.5: 实现 `api.deleteQuestion` 函数
  - [x] SubTask 3.6: 实现 `api.getTags` 函数
  - [x] SubTask 3.7: 实现 `api.splitImage` 函数
  - [x] SubTask 3.8: 实现 `api.checkScreenshot` 函数
  - [x] SubTask 3.9: 实现 `api.consumeScreenshot` 函数

- [x] Task 4: 实现 image-handler.js 图片处理模块
  - [x] SubTask 4.1: 实现 `handleImagePaste` 函数
  - [x] SubTask 4.2: 实现 `updateImageDisplay` 函数
  - [x] SubTask 4.3: 实现 `updateImageSize` 函数
  - [x] SubTask 4.4: 实现字框标注相关函数

- [x] Task 5: 实现 content-renderer.js 内容渲染模块
  - [x] SubTask 5.1: 实现 `renderContentList` 函数
  - [x] SubTask 5.2: 实现 `renderPreview` 函数
  - [x] SubTask 5.3: 实现 `renderTags` 函数
  - [x] SubTask 5.4: 实现 `renderSubQuestions` 函数

- [x] Task 6: 实现 state.js 状态管理模块
  - [x] SubTask 6.1: 实现 `Store` 类
  - [x] SubTask 6.2: 实现 `getState` 方法
  - [x] SubTask 6.3: 实现 `setState` 方法
  - [x] SubTask 6.4: 实现 `subscribe` 方法

- [x] Task 7: 重构 index.html
  - [x] SubTask 7.1: 添加模块引用
  - [x] SubTask 7.2: 替换工具函数调用
  - [x] SubTask 7.3: 替换 API 调用
  - [x] SubTask 7.4: 替换图片处理函数
  - [x] SubTask 7.5: 替换渲染函数
  - [x] SubTask 7.6: 验证所有功能正常

- [x] Task 8: 重构 browse.html
  - [x] SubTask 8.1: 添加模块引用
  - [x] SubTask 8.2: 替换工具函数调用
  - [x] SubTask 8.3: 替换 API 调用
  - [x] SubTask 8.4: 替换图片处理函数
  - [x] SubTask 8.5: 替换渲染函数
  - [x] SubTask 8.6: 验证所有功能正常

- [x] Task 9: 重构 print.html
  - [x] SubTask 9.1: 添加模块引用
  - [x] SubTask 9.2: 替换工具函数调用
  - [x] SubTask 9.3: 替换渲染函数
  - [x] SubTask 9.4: 验证所有功能正常

- [x] Task 10: 全面测试验证
  - [x] SubTask 10.1: 测试 index.html 所有功能
  - [x] SubTask 10.2: 测试 browse.html 所有功能
  - [x] SubTask 10.3: 测试 print.html 所有功能
  - [x] SubTask 10.4: 验证无 JavaScript 报错
  - [x] SubTask 10.5: 验证功能与原来完全一致

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1, Task 3]
- [Task 5] depends on [Task 1, Task 2]
- [Task 6] depends on [Task 1]
- [Task 7] depends on [Task 2, Task 3, Task 4, Task 5, Task 6]
- [Task 8] depends on [Task 2, Task 3, Task 4, Task 5, Task 6]
- [Task 9] depends on [Task 2, Task 3, Task 5]
- [Task 10] depends on [Task 7, Task 8, Task 9]
