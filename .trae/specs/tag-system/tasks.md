# Tasks

- [x] Task 1: 创建 TagSystem 核心类结构
  - [x] SubTask 1.1: 创建 TagSystem 类框架，包含 __init__ 方法
  - [x] SubTask 1.2: 实现数据加载和保存方法（_load_data, _save_data）
  - [x] SubTask 1.3: 实现标签树维护方法（_update_tag_tree, _ensure_parent_tags）

- [x] Task 2: 实现单个标签操作
  - [x] SubTask 2.1: 实现 add_tag 方法（添加标签到记录）
  - [x] SubTask 2.2: 实现 remove_tag 方法（删除记录标签）
  - [x] SubTask 2.3: 实现 update_tag 方法（修改记录标签）
  - [x] SubTask 2.4: 实现 get_tags 方法（获取记录所有标签）

- [x] Task 3: 实现基础搜索功能
  - [x] SubTask 3.1: 实现 search 方法（支持 exact, prefix, suffix, contains 模式）
  - [x] SubTask 3.2: 实现 search_by_regex 方法（正则表达式搜索）
  - [x] SubTask 3.3: 实现 get_records_with_tag 方法（获取包含某标签的所有记录）

- [x] Task 4: 实现复杂搜索表达式解析器（逻辑运算符）
  - [x] SubTask 4.1: 实现搜索表达式词法分析器（Tokenization）
  - [x] SubTask 4.2: 实现搜索表达式语法分析器（Parsing）- 支持 AND, OR, NOT, 分组
  - [x] SubTask 4.3: 实现 search_with_operators 方法（支持逻辑运算符组合）
  - [x] SubTask 4.4: 测试各种逻辑运算符组合

- [x] Task 5: 实现批量操作
  - [x] SubTask 5.1: 实现 batch_add_tag 方法（批量添加标签）
  - [x] SubTask 5.2: 实现 batch_remove_tag 方法（批量删除标签）

- [x] Task 6: 实现标签树和层级管理
  - [x] SubTask 6.1: 实现 get_tag_tree 方法（获取完整标签树）
  - [x] SubTask 6.2: 实现 get_all_tags 方法（获取所有标签列表）
  - [x] SubTask 6.3: 实现 delete_tag_from_system 方法（删除系统中的标签）

- [x] Task 7: 创建使用示例
  - [x] SubTask 7.1: 创建 example.py 演示基本用法
  - [x] SubTask 7.2: 演示多级标签创建和查询
  - [x] SubTask 7.3: 演示各种搜索方式（包括逻辑运算符）

# Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 1
- Task 4 依赖 Task 3
- Task 5 依赖 Task 2
- Task 6 依赖 Task 1
- Task 7 依赖 Task 1, Task 2, Task 3, Task 4, Task 5, Task 6
