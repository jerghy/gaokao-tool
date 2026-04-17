# 训练题目浏览与打印系统 Spec

## Why
用户需要一个专门浏览和管理 AI 生成的训练题目的界面，能够按能力点筛选、搜索、预览训练题目，并支持批量打印功能。当前系统已有错题浏览和打印功能，需要扩展支持训练题目（`chinese_modern_text_training` 字段）。

## What Changes
- 新增训练题目浏览页面 `training.html`，模仿 `browse.html` 的三栏布局
- 新增训练题目打印页面 `training-print.html`，模仿 `print.html` 的打印布局
- 后端新增 API 接口支持训练题目的查询和筛选
- 支持按能力点（abilityPoint）标签树筛选训练题目

## Impact
- Affected specs: 无
- Affected code:
  - `app.py` - 新增训练题目相关 API
  - `static/training.html` - 新建训练题目浏览页面
  - `static/training-print.html` - 新建训练题目打印页面

## ADDED Requirements

### Requirement: 训练题目浏览页面
系统应提供训练题目浏览页面，包含以下功能：

#### Scenario: 三栏布局浏览
- **WHEN** 用户访问 `/training.html`
- **THEN** 显示三栏布局：左侧标签树、中间训练题目列表、右侧训练题目详情

#### Scenario: 能力点标签树
- **WHEN** 页面加载完成
- **THEN** 左侧显示从所有训练题目的 `abilityPoint` 字段提取的标签树
- **AND** 支持展开/折叠层级
- **AND** 点击标签可筛选训练题目

#### Scenario: 训练题目列表
- **WHEN** 用户选择标签或搜索
- **THEN** 中间区域显示匹配的训练题目卡片
- **AND** 每个卡片显示：所属题目ID、能力点、问题预览
- **AND** 支持多选（复选框）

#### Scenario: 搜索功能
- **WHEN** 用户在搜索框输入关键词
- **THEN** 支持 Anki 搜索语法（与 browse.html 相同）
- **AND** 支持按能力点、问题内容、材料内容搜索

#### Scenario: 训练题目详情
- **WHEN** 用户点击某个训练题目
- **THEN** 右侧显示完整内容：材料、问题、能力点、答案解析

#### Scenario: 右键菜单打印
- **WHEN** 用户多选训练题目后右键
- **THEN** 显示上下文菜单，包含"打印选中题目"选项
- **AND** 点击后跳转到打印页面

### Requirement: 训练题目打印页面
系统应提供训练题目打印页面：

#### Scenario: 打印预览
- **WHEN** 用户从浏览页面跳转到打印页面
- **THEN** 显示选中的训练题目打印预览
- **AND** 每个训练题目显示：材料、问题、答案区域

#### Scenario: 打印格式
- **WHEN** 用户执行打印
- **THEN** 训练题目按卡片格式打印
- **AND** 材料部分有背景色区分
- **AND** 问题部分突出显示
- **AND** 答案部分可折叠或单独显示

### Requirement: 后端 API
系统应提供训练题目相关 API：

#### Scenario: 获取训练题目列表
- **WHEN** 前端请求 `/api/training-items`
- **THEN** 返回所有训练题目列表
- **AND** 支持分页和搜索参数

#### Scenario: 获取能力点标签树
- **WHEN** 前端请求 `/api/training-ability-tags`
- **THEN** 返回从 abilityPoint 字段提取的标签树结构
