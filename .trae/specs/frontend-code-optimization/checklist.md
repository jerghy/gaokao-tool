# Checklist

## 冗余函数移除
- [x] index.html 中 `escapeHtml` 包装函数已移除
- [x] index.html 中 `renderLatex` 包装函数已移除
- [x] index.html 中 `processTextWithLatex` 包装函数已移除
- [x] index.html 中 `renderRichtext` 包装函数已移除
- [x] browse.html 中所有冗余包装函数已移除
- [x] print.html 中所有冗余包装函数已移除（无需修改，有独立实现）

## API 错误处理
- [x] `api.js` 添加了通用 `request` 方法
- [x] 所有 API 调用都有错误处理
- [x] 错误格式统一

## 功能验证
- [x] index.html 所有功能正常
- [x] browse.html 所有功能正常
- [x] print.html 所有功能正常
- [x] 无 JavaScript 报错
- [x] 题目录入功能正常
- [x] 图片上传功能正常
- [x] 字框标注功能正常
- [x] 图片分割功能正常
- [x] 标签管理功能正常
- [x] 搜索功能正常
