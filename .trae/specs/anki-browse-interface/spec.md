# Anki 风格浏览界面 - 产品需求文档

## Overview
- **Summary**: 为现有错题收录系统添加一个类似 Anki 的浏览界面，包含左侧标签树、中间错题列表和右侧编辑区域，实现错题的高效浏览、筛选和编辑功能。
- **Purpose**: 解决当前系统只能录入而无法浏览和编辑已有错题的问题，提供一个直观的界面来管理和组织错题资源。
- **Target Users**: 学生、教师等需要管理错题资源的用户。

## Goals
- 提供三栏式布局的浏览界面（标签树、错题列表、编辑区域）
- 实现标签树的层级展示和选择功能
- 支持按标签筛选和搜索错题（支持题目内容和标签搜索，支持多级标签）
- 支持多个标签的组合筛选（AND/OR）
- 提供错题的完整编辑功能（题目、答案、标签）
- 支持错题删除功能
- 支持多选错题进行批量操作（如批量加标签）
- 集成现有的 tag_system.py 标签系统

## Non-Goals (Out of Scope)
- 不实现 Anki 的记忆算法和复习功能
- 不实现错题的打印功能（已有 print.html 处理）
- 不实现用户认证和多用户功能
- 不实现错题的导出功能

## Background & Context
- 现有系统已实现错题的录入功能，使用 Flask 后端，数据存储在 data/ 目录的 JSON 文件中
- 已提供 tag_system.py 作为标签管理的轮子，支持层级标签、搜索、批量操作等功能
- 现有 index.html 提供了丰富的内容编辑组件（文本、图片、LaTeX 支持），可以复用

## Functional Requirements
- **FR-1**: 提供三栏式布局的浏览界面
- **FR-2**: 左侧展示可展开/折叠的标签树
- **FR-3**: 点击标签可筛选显示对应标签的错题
- **FR-4**: 中间区域显示错题列表，支持搜索功能（题目内容和标签搜索）
- **FR-5**: 支持多个标签的组合筛选（AND/OR）
- **FR-6**: 右侧区域显示和编辑选中的错题
- **FR-7**: 支持编辑错题的题目、答案和标签
- **FR-8**: 支持错题删除功能
- **FR-9**: 支持多选错题进行批量操作（如批量加标签）
- **FR-10**: 后端集成 tag_system.py 提供标签 API

## Non-Functional Requirements
- **NFR-1**: 界面响应式，在常见屏幕尺寸下可用
- **NFR-2**: 错题加载和搜索响应时间 < 500ms
- **NFR-3**: 保持与现有系统的风格一致性

## Constraints
- **Technical**: 使用现有的 Flask 框架和 tag_system.py，前端使用原生 JavaScript（不引入新框架）
- **Business**: 必须复用现有的数据存储格式和内容编辑组件
- **Dependencies**: 依赖现有的 app.py、tag_system.py 和 index.html 中的编辑逻辑

## Assumptions
- tag_system.py 的功能可以满足需求，可能需要轻微调整
- 现有数据格式保持不变
- 用户已经安装了项目所需的 Python 依赖

## Acceptance Criteria

### AC-1: 三栏布局展示
- **Given**: 用户访问浏览界面
- **When**: 页面加载完成
- **Then**: 显示左侧标签树、中间错题列表、右侧编辑区域的三栏布局
- **Verification**: `human-judgment`

### AC-2: 标签树展示和交互
- **Given**: 系统中存在标签数据
- **When**: 用户浏览左侧标签树
- **Then**: 标签以层级结构展示，支持展开/折叠
- **Verification**: `programmatic`

### AC-3: 按标签筛选错题
- **Given**: 用户在浏览界面
- **When**: 用户点击某个标签
- **Then**: 中间列表只显示带有该标签的错题
- **Verification**: `programmatic`

### AC-4: 错题列表展示
- **Given**: 系统中存在错题数据
- **When**: 页面加载或用户进行筛选/搜索
- **Then**: 中间区域显示错题列表，无筛选时显示全部
- **Verification**: `programmatic`

### AC-5: 搜索错题功能
- **Given**: 用户在浏览界面
- **When**: 用户在搜索框输入关键词
- **Then**: 中间列表显示匹配的错题
- **Verification**: `programmatic`

### AC-6: 错题编辑功能
- **Given**: 用户选中了一个错题
- **When**: 用户在右侧编辑区域修改内容并保存
- **Then**: 错题内容被更新并持久化
- **Verification**: `programmatic`

### AC-7: 标签编辑功能
- **Given**: 用户正在编辑一个错题
- **When**: 用户添加或删除标签
- **Then**: 标签变更被保存，同时更新 tag_system 数据
- **Verification**: `programmatic`

### AC-8: 后端标签 API
- **Given**: 系统运行中
- **When**: 前端调用标签相关 API
- **Then**: API 正确响应并操作 tag_system
- **Verification**: `programmatic`

### AC-9: 组合筛选功能
- **Given**: 用户在浏览界面
- **When**: 用户选择多个标签并设置 AND/OR 逻辑
- **Then**: 中间列表显示符合组合筛选条件的错题
- **Verification**: `programmatic`

### AC-10: 错题删除功能
- **Given**: 用户选中了一个错题
- **When**: 用户执行删除操作
- **Then**: 错题被从系统中删除，tag_system 数据同步更新
- **Verification**: `programmatic`

### AC-11: 多选和批量操作功能
- **Given**: 用户在错题列表中
- **When**: 用户多选多个错题并右键执行批量操作（如批量加标签）
- **Then**: 批量操作成功执行，所有选中的错题都被更新
- **Verification**: `programmatic`

### AC-12: 搜索功能增强
- **Given**: 用户在浏览界面
- **When**: 用户在搜索框输入关键词
- **Then**: 中间列表显示题目内容或标签匹配的错题，支持多级标签搜索
- **Verification**: `programmatic`
