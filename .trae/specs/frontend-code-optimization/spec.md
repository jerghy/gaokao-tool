# 前端代码优化 Spec

## Why
当前前端代码虽然已经提取了公共模块，但仍存在冗余包装函数、CSS重复、API缺少错误处理等问题。需要进一步优化以提高代码质量和可维护性。

## What Changes
- 移除 HTML 中的冗余包装函数，直接使用公共模块
- 提取公共 CSS 到独立文件
- 为 API 添加统一错误处理
- **无破坏性变更** - 所有功能保持完全一致

## Impact
- Affected specs: 
  - frontend-progressive-refactor（基于此规范继续优化）
- Affected code:
  - `static/index.html` - 移除冗余函数
  - `static/browse.html` - 移除冗余函数
  - `static/print.html` - 移除冗余函数
  - `static/js/api.js` - 添加错误处理
  - 新增 `static/css/common.css` - 公共样式

## ADDED Requirements

### Requirement: 移除冗余包装函数
HTML 中不应存在只是简单调用公共模块的包装函数。

#### Scenario: 直接使用公共模块
- **WHEN** HTML 中需要使用工具函数
- **THEN** 直接调用 `Utils.escapeHtml()` 而非 `escapeHtml()`

### Requirement: 公共 CSS 提取
系统应将重复的 CSS 样式提取到公共文件。

#### Scenario: CSS 文件结构
- **WHEN** 提取公共样式
- **THEN** 创建以下文件：
  - `static/css/common.css` - 公共样式
  - 各 HTML 文件引用公共样式

### Requirement: API 错误处理
API 模块应提供统一的错误处理机制。

#### Scenario: 错误处理
- **WHEN** API 调用失败
- **THEN** 统一处理错误，返回标准错误格式

## MODIFIED Requirements
无

## REMOVED Requirements
无
