# 纯标签系统（Tag System）Spec

## Why

需要一个可复用的 Python 标签系统"轮子"，实现类似 Anki 的标签功能。后续应用将使用该系统进行错题管理、题目分类等场景。需要支持多级标签、复杂搜索（包含逻辑运算符）、批量操作等特性，并留有清晰接口供后续应用调用。

## What Changes

* 创建独立的 TagSystem Python 库

* 实现多级标签支持（使用 `::` 分隔，如 `数学::代数::一元二次方程`）

* 实现复杂搜索能力：精确匹配、前缀匹配、后缀匹配、包含匹配、正则表达式匹配

* 实现逻辑运算符支持：AND（与）、OR（或）、NOT（非）、分组 `(...)`

* 实现标签的增删改查操作

* 实现批量标签操作

* 提供清晰 API 接口供后续应用调用

## Impact

* 新增文件：tag\_system.py（核心库）

* 数据存储：使用 JSON 文件存储标签数据

* 后续应用可导入该库使用标签功能

## ADDED Requirements

### Requirement: 多级标签支持

系统应当支持多级标签结构，使用 `::` 作为分隔符。

#### Scenario: 创建多级标签

* **WHEN** 用户创建标签 `数学::代数::一元二次方程`

* **THEN** 系统解析为三级标签结构

* **AND** 父标签 `数学` 包含子标签 `代数`

* **AND** 标签 `代数` 包含子标签 `一元二次方程`

#### Scenario: 查询子标签

* **WHEN** 用户查询标签 `数学` 的所有子标签

* **THEN** 返回 `代数` 及其所有子标签

* **AND** 包含嵌套层级的完整路径

### Requirement: 复杂搜索功能

系统应当提供多种搜索方式和逻辑运算符组合。

#### Scenario: 精确匹配

* **WHEN** 用户搜索精确标签名 `数学`

* **THEN** 返回所有包含该精确标签的记录

#### Scenario: 前缀匹配

* **WHEN** 用户使用前缀搜索 `数学::`

* **THEN** 返回所有以 `数学::` 开头的标签记录

#### Scenario: 后缀匹配

* **WHEN** 用户使用后缀搜索 `::一元二次方程`

* **THEN** 返回所有以 `::一元二次方程` 结尾的标签记录

#### Scenario: 包含匹配

* **WHEN** 用户使用包含搜索 `代数`

* **THEN** 返回所有标签路径中包含 `代数` 的记录

#### Scenario: 正则表达式匹配

* **WHEN** 用户使用正则搜索 `数学::.*::.*`

* **THEN** 返回所有匹配该正则表达式的标签记录

#### Scenario: AND 逻辑运算

* **WHEN** 用户搜索 `数学 AND 重要` 或 `数学 重要`（空格表示AND）

* **THEN** 返回同时包含 `数学` 和 `重要` 标签的记录

#### Scenario: OR 逻辑运算

* **WHEN** 用户搜索 `数学 OR 英语`

* **THEN** 返回包含 `数学` 或包含 `英语` 或同时包含两者的记录

#### Scenario: NOT 逻辑运算

* **WHEN** 用户搜索 `数学 NOT 几何` 或 `数学 -几何`

* **THEN** 返回包含 `数学` 但不包含 `几何` 的记录

#### Scenario: 分组运算

* **WHEN** 用户搜索 `(数学 OR 英语) AND 重要`

* **THEN** 返回同时包含 `重要` 且包含 `数学` 或 `英语` 的记录

#### Scenario: 混合复杂搜索

* **WHEN** 用户搜索 `数学:: AND (重要 OR 复习) NOT 已删除`

* **THEN** 返回满足复杂逻辑条件的记录

### Requirement: 单个标签操作

系统应当支持单个标签的增删改查。

#### Scenario: 添加标签到记录

* **WHEN** 用户为某记录添加标签 `数学::代数`

* **THEN** 该记录关联该标签

* **AND** 自动创建父标签层级（如需要）

#### Scenario: 删除记录标签

* **WHEN** 用户删除某记录的标签 `数学::代数`

* **THEN** 该记录取消关联该标签

* **AND** 保留其他标签不受影响

#### Scenario: 修改记录标签

* **WHEN** 用户将记录标签从 `数学::代数` 修改为 `数学::几何`

* **THEN** 原标签关联被移除

* **AND** 新标签关联被添加

### Requirement: 批量标签操作

系统应当支持批量添加和删除标签。

#### Scenario: 批量添加标签

* **WHEN** 用户选择多条记录并添加标签 `重要`

* **THEN** 所有选中记录都关联该标签

#### Scenario: 批量删除标签

* **WHEN** 用户选择多条记录并删除标签 `重要`

* **THEN** 所有选中记录都取消关联该标签

### Requirement: 标签层级管理

系统应当提供标签层级管理功能。

#### Scenario: 获取标签树

* **WHEN** 用户请求获取完整标签树

* **THEN** 返回树形结构展示所有标签及其层级关系

#### Scenario: 获取某记录的所有标签

* **WHEN** 用户查询某记录关联的所有标签

* **THEN** 返回该记录的所有标签（包括完整路径）

## API 接口设计

### 核心类：TagSystem

```python
class TagSystem:
    def __init__(self, data_path: str = "tags_data.json")

    def add_tag(self, record_id: str, tag: str) -> bool
    def remove_tag(self, record_id: str, tag: str) -> bool
    def update_tag(self, record_id: str, old_tag: str, new_tag: str) -> bool
    def get_tags(self, record_id: str) -> List[str]

    def search(self, query: str, match_type: str = "exact") -> List[str]
    def search_by_regex(self, regex_pattern: str) -> List[str]
    def search_with_operators(self, query: str) -> List[str]

    def batch_add_tag(self, record_ids: List[str], tag: str) -> Dict[str, bool]
    def batch_remove_tag(self, record_ids: List[str], tag: str) -> Dict[str, bool]

    def get_tag_tree(self) -> Dict
    def get_all_tags(self) -> List[str]
    def get_records_with_tag(self, tag: str) -> List[str]

    def delete_tag_from_system(self, tag: str) -> bool
```

### 搜索类型枚举

```python
class MatchType:
    EXACT = "exact"       # 精确匹配
    PREFIX = "prefix"     # 前缀匹配
    SUFFIX = "suffix"     # 后缀匹配
    CONTAINS = "contains"  # 包含匹配
    REGEX = "regex"       # 正则匹配
```

### 搜索运算符

* `空格` 或 `AND`：逻辑与（同时满足）

* `OR` 或 `|`：逻辑或（满足任一）

* `NOT` 或 `-`：逻辑非（排除）

* `(` `)`：分组运算

* 示例：`数学 AND (重要 OR 复习) NOT 已删除`

## 数据结构

### 标签数据 JSON 格式

```json
{
  "records": {
    "record_001": ["数学::代数::一元二次方程", "重要"],
    "record_002": ["数学::几何::三角形", "复习"],
    "record_003": ["英语::阅读::科技"]
  },
  "tag_tree": {
    "数学": {
      "children": {
        "代数": {
          "children": {
            "一元二次方程": {}
          }
        },
        "几何": {
          "children": {
            "三角形": {}
          }
        }
      }
    },
    "英语": {
      "children": {
        "阅读": {
          "children": {
            "科技": {}
          }
        }
      }
    },
    "重要": {},
    "复习": {}
  }
}
```

## 技术方案

### 文件结构

* `tag_system.py` - 核心标签系统库

* `example.py` - 使用示例

### 依赖

* Python 3.6+

* 仅使用标准库（json, re, os, copy）

### 特性

* 数据持久化到 JSON 文件

* 自动创建父标签层级

* 支持空记录ID（用于管理标签本身）

* 复杂搜索表达式解析器

* 线程安全（文件锁）

