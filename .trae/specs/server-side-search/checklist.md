# Checklist

## 搜索引擎模块验证

- [x] `search_engine.py` 文件创建成功
- [x] 词法分析器正确解析所有 token 类型（TAG, TEXT, PHRASE, AND, OR, NOT, LPAREN, RPAREN）
- [x] 语法分析器正确构建 AST 结构
- [x] 标签搜索 `tag:xxx` 功能正常
- [x] 排除标签 `-tag:xxx` 功能正常
- [x] 文本搜索功能正常
- [x] 精确短语搜索 `"xxx"` 功能正常
- [x] AND 逻辑搜索功能正常
- [x] OR 逻辑搜索功能正常
- [x] NOT 逻辑搜索功能正常
- [x] 括号分组搜索功能正常
- [x] 通配符搜索功能正常
- [x] 复杂组合搜索功能正常

## API 验证

- [x] `/api/questions?search=xxx` 端点正常响应
- [x] 搜索结果正确分页
- [x] 空搜索参数返回所有题目
- [x] 搜索结果包含正确的 total 和 total_pages

## browse.html 验证

- [x] 搜索框输入后正确调用服务端 API
- [x] 搜索结果正确显示
- [x] 前端搜索相关函数已移除
- [x] 防抖功能正常工作
- [x] 分页功能与搜索兼容

## print.html 验证

- [x] 搜索框输入后正确调用服务端 API
- [x] 搜索结果正确显示
- [x] 前端搜索相关函数已移除
- [x] 标签筛选与搜索兼容
- [x] 题目选择功能正常
