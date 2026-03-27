# 服务端搜索实现 Spec

## Why

当前 `browse.html` 和 `print.html` 的搜索功能完全在前端 JavaScript 实现，每次搜索需要加载大量数据到浏览器内存，性能较差且无法利用服务端索引优化。需要将 Anki 风格的搜索语法实现迁移到 Python 服务端，让前端仅请求搜索结果。

## What Changes

- 创建 Python 搜索模块，实现 Anki 风格搜索语法解析与执行
- 修改 `/api/questions` API 支持 `search` 查询参数
- 修改 `browse.html` 使用服务端搜索 API
- 修改 `print.html` 使用服务端搜索 API
- 移除前端 JavaScript 中的搜索语法解析和过滤逻辑

## Impact

- 新增文件：`search_engine.py`（搜索引擎模块）
- 修改文件：`app.py`（API 端点扩展）
- 修改文件：`static/browse.html`（前端搜索调用方式）
- 修改文件：`static/print.html`（前端搜索调用方式）
- 受影响功能：题目列表查询、题目筛选

## ADDED Requirements

### Requirement: Python 搜索引擎模块

系统应当提供独立的搜索引擎模块，支持 Anki 风格的搜索语法。

#### Scenario: 标签搜索
- **WHEN** 用户输入 `tag:数学`
- **THEN** 返回所有包含"数学"标签的题目

#### Scenario: 排除标签
- **WHEN** 用户输入 `-tag:已掌握` 或 `tag:-已掌握`
- **THEN** 返回不包含"已掌握"标签的题目

#### Scenario: 文本搜索
- **WHEN** 用户输入 `函数`
- **THEN** 返回题目内容或答案中包含"函数"的题目

#### Scenario: 精确短语搜索
- **WHEN** 用户输入 `"一元二次方程"`
- **THEN** 返回包含精确短语"一元二次方程"的题目

#### Scenario: AND 逻辑
- **WHEN** 用户输入 `tag:数学 tag:重要` 或 `tag:数学 AND tag:重要`
- **THEN** 返回同时包含"数学"和"重要"标签的题目

#### Scenario: OR 逻辑
- **WHEN** 用户输入 `tag:数学 OR tag:物理`
- **THEN** 返回包含"数学"或"物理"标签的题目

#### Scenario: NOT 逻辑
- **WHEN** 用户输入 `tag:数学 NOT tag:已掌握`
- **THEN** 返回包含"数学"但不包含"已掌握"标签的题目

#### Scenario: 括号分组
- **WHEN** 用户输入 `(tag:数学 OR tag:物理) tag:重要`
- **THEN** 返回包含"重要"且同时包含"数学"或"物理"的题目

#### Scenario: 通配符搜索
- **WHEN** 用户输入 `tag:数学::*`
- **THEN** 返回所有"数学"层级下的标签题目

#### Scenario: 复杂组合搜索
- **WHEN** 用户输入 `(tag:生物 OR tag:化学) tag:重要 -tag:已掌握`
- **THEN** 返回满足复杂逻辑条件的题目

### Requirement: API 搜索参数支持

`/api/questions` API 应当支持 `search` 查询参数。

#### Scenario: 带搜索参数的请求
- **WHEN** 客户端请求 `/api/questions?search=tag:数学`
- **THEN** 服务端返回匹配搜索条件的题目列表
- **AND** 返回结果包含分页信息

#### Scenario: 空搜索参数
- **WHEN** 客户端请求 `/api/questions?search=`
- **THEN** 服务端返回所有题目（等同于无搜索参数）

### Requirement: 前端搜索调用改造

前端页面应当使用服务端搜索 API，移除本地搜索逻辑。

#### Scenario: browse.html 搜索
- **WHEN** 用户在搜索框输入内容
- **THEN** 前端发送请求到 `/api/questions?search=xxx`
- **AND** 服务端返回过滤后的结果

#### Scenario: print.html 搜索
- **WHEN** 用户在搜索框输入内容
- **THEN** 前端发送请求到 `/api/questions?search=xxx`
- **AND** 服务端返回过滤后的结果

## MODIFIED Requirements

### Requirement: 题目查询 API

原有 `/api/questions` API 需要扩展支持搜索参数。

**修改后**：
- 支持 `search` 参数进行搜索过滤
- 搜索在服务端执行，返回过滤后的分页结果
- 保持原有分页参数 `page` 和 `page_size`

## REMOVED Requirements

### Requirement: 前端搜索语法解析

**Reason**: 搜索逻辑迁移到服务端，前端不再需要解析搜索语法。

**Migration**: 
- 移除 `tokenizeSearchQuery()` 函数
- 移除 `parseTokensToAST()` 函数
- 移除 `evaluateAST()` 函数
- 移除 `evaluateSearchQuery()` 函数
- 移除 `filterQuestionsLocal()` 函数
- 移除相关辅助函数（`matchTag`, `matchText`, `matchPhrase`, `createRegex` 等）

## 搜索语法规范

### 支持的语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `tag:xxx` | 标签搜索 | `tag:数学` |
| `-tag:xxx` | 排除标签 | `-tag:已掌握` |
| `文本` | 全文搜索 | `函数` |
| `"短语"` | 精确短语 | `"一元二次方程"` |
| `AND` 或空格 | 逻辑与 | `tag:数学 tag:重要` |
| `OR` | 逻辑或 | `tag:数学 OR tag:物理` |
| `NOT` 或 `-` | 逻辑非 | `tag:数学 NOT tag:简单` |
| `()` | 分组 | `(tag:数学 OR tag:物理) tag:重要` |
| `*` | 通配符 | `tag:数学::*` |
| `_` | 单字符通配 | `tag:数学_代数` |

## 技术方案

### 文件结构

```
d:\space\html\print\
├── search_engine.py     # 新增：搜索引擎模块
├── app.py               # 修改：扩展 API
├── tag_system.py        # 保留：标签系统
└── static/
    ├── browse.html      # 修改：前端搜索调用
    └── print.html       # 修改：前端搜索调用
```

### 搜索引擎模块设计

```python
class SearchEngine:
    def __init__(self, data_dir: str, tag_system: TagSystem)
    
    def search(self, query: str, page: int = 1, page_size: int = 50) -> dict:
        """执行搜索，返回分页结果"""
        
    def _tokenize(self, query: str) -> List[Token]
        """词法分析：将查询字符串转换为 token 列表"""
        
    def _parse(self, tokens: List[Token]) -> ASTNode
        """语法分析：将 token 列表转换为 AST"""
        
    def _evaluate(self, node: ASTNode, questions: List[dict]) -> List[dict]
        """执行搜索：根据 AST 过滤题目"""
```

### API 响应格式

```json
{
  "questions": [...],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2,
  "search_query": "tag:数学"
}
```
