# Checklist

## 核心类结构
- [x] TagSystem 类可以正确初始化
- [x] 数据可以从 JSON 文件加载
- [x] 数据可以保存到 JSON 文件
- [x] 标签树可以正确维护

## 单个标签操作
- [x] add_tag 方法可以正确添加标签
- [x] remove_tag 方法可以正确删除标签
- [x] update_tag 方法可以正确修改标签
- [x] get_tags 方法可以正确获取记录的所有标签
- [x] 多级标签自动创建父标签层级

## 基础搜索功能
- [x] 精确匹配（exact）搜索正常工作
- [x] 前缀匹配（prefix）搜索正常工作
- [x] 后缀匹配（suffix）搜索正常工作
- [x] 包含匹配（contains）搜索正常工作
- [x] 正则表达式（regex）搜索正常工作
- [x] get_records_with_tag 方法正确返回包含指定标签的记录

## 复杂搜索表达式（逻辑运算符）
- [x] AND 运算符（空格或 AND）正常工作
- [x] OR 运算符（| 或 OR）正常工作
- [x] NOT 运算符（- 或 NOT）正常工作
- [x] 分组运算 ( ... ) 正常工作
- [x] 混合表达式如 `(数学 OR 英语) AND 重要 NOT 已删除` 正确计算

## 批量操作
- [x] batch_add_tag 方法可以批量添加标签
- [x] batch_remove_tag 方法可以批量删除标签

## 标签树和层级管理
- [x] get_tag_tree 方法返回正确的树形结构
- [x] get_all_tags 方法返回所有标签列表
- [x] delete_tag_from_system 方法可以删除标签（同时从所有记录中移除）

## 数据结构正确性
- [x] JSON 数据格式符合 spec 定义
- [x] 标签树结构正确维护层级关系
- [x] 记录与标签的关联关系正确

## 示例代码
- [x] example.py 演示了基本用法
- [x] 演示了多级标签的创建和查询
- [x] 演示了各种搜索方式（包括逻辑运算符）
