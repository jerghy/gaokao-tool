# Tasks

- [x] Task 1: 创建 Python 搜索引擎模块 `search_engine.py`
  - [ ] SubTask 1.1: 实现 Token 数据类和 TokenType 枚举
  - [ ] SubTask 1.2: 实现词法分析器 `_tokenize()` 方法
  - [ ] SubTask 1.3: 实现 AST 节点类（TagNode, TextNode, PhraseNode, AndNode, OrNode, NotNode）
  - [ ] SubTask 1.4: 实现语法分析器 `_parse()` 方法
  - [ ] SubTask 1.5: 实现搜索执行器 `_evaluate()` 方法
  - [ ] SubTask 1.6: 实现主搜索接口 `search()` 方法
  - [ ] SubTask 1.7: 实现通配符匹配和标签层级搜索

- [x] Task 2: 修改 `app.py` 扩展 `/api/questions` API
  - [ ] SubTask 2.1: 导入 SearchEngine 模块
  - [ ] SubTask 2.2: 初始化 SearchEngine 实例
  - [ ] SubTask 2.3: 修改 `get_questions()` 函数支持 `search` 参数
  - [ ] SubTask 2.4: 集成搜索逻辑到分页流程

- [x] Task 3: 修改 `browse.html` 使用服务端搜索
  - [ ] SubTask 3.1: 修改 `applyFilters()` 函数调用服务端 API
  - [ ] SubTask 3.2: 移除前端搜索相关函数（tokenizeSearchQuery, parseTokensToAST, evaluateAST, filterQuestionsLocal 等）
  - [ ] SubTask 3.3: 移除前端 matchTag, matchText, matchPhrase, createRegex 等辅助函数
  - [ ] SubTask 3.4: 更新搜索框事件处理逻辑

- [x] Task 4: 修改 `print.html` 使用服务端搜索
  - [ ] SubTask 4.1: 修改 `loadQuestions()` 函数支持搜索参数
  - [ ] SubTask 4.2: 修改 `applySearchFilter()` 函数调用服务端 API
  - [ ] SubTask 4.3: 移除前端搜索相关函数（tokenizeSearchQuery, parseTokensToAST, evaluateAST, evaluateSearchQuery 等）
  - [ ] SubTask 4.4: 移除前端 matchTag, matchText, matchPhrase, createRegex, getEffectiveTags 等辅助函数

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 2]
- [Task 3] 和 [Task 4] 可以并行执行
