# Tasks

- [x] Task 1: 移除 index.html 冗余包装函数
  - [x] SubTask 1.1: 移除 `escapeHtml` 包装函数
  - [x] SubTask 1.2: 移除 `renderLatex` 包装函数
  - [x] SubTask 1.3: 移除 `processTextWithLatex` 包装函数
  - [x] SubTask 1.4: 移除 `renderRichtext` 包装函数
  - [x] SubTask 1.5: 替换所有调用为 `Utils.xxx()`
  - [x] SubTask 1.6: 验证无报错

- [x] Task 2: 移除 browse.html 冗余包装函数
  - [x] SubTask 2.1: 移除 `escapeHtml` 包装函数
  - [x] SubTask 2.2: 移除 `renderLatex` 包装函数
  - [x] SubTask 2.3: 移除 `processTextWithLatex` 包装函数
  - [x] SubTask 2.4: 移除 `renderRichtext` 包装函数
  - [x] SubTask 2.5: 替换所有调用为 `Utils.xxx()`
  - [x] SubTask 2.6: 验证无报错

- [x] Task 3: 移除 print.html 冗余包装函数
  - [x] SubTask 3.1: 检查是否有冗余包装函数
  - [x] SubTask 3.2: print.html 有独立实现，无需修改
  - [x] SubTask 3.3: 验证无报错

- [x] Task 4: 为 API 添加错误处理
  - [x] SubTask 4.1: 添加 `request` 通用方法
  - [x] SubTask 4.2: 添加错误拦截逻辑
  - [x] SubTask 4.3: 保持现有接口不变
  - [x] SubTask 4.4: 验证无报错

- [ ] Task 5: 提取公共 CSS（可选）
  - [ ] SubTask 5.1: 分析公共样式
  - [ ] SubTask 5.2: 创建 `common.css`
  - [ ] SubTask 5.3: 更新 HTML 引用

- [x] Task 6: 全面测试验证
  - [x] SubTask 6.1: 测试 index.html 所有功能
  - [x] SubTask 6.2: 测试 browse.html 所有功能
  - [x] SubTask 6.3: 测试 print.html 所有功能
  - [x] SubTask 6.4: 验证无 JavaScript 报错

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 6] depends on [Task 1, Task 2, Task 3, Task 4]
