# 前端架构改进 Spec

## Why
当前前端代码存在函数重复、公共模块未使用、状态管理分散等问题，影响后续开发效率和代码可维护性。需要进一步优化架构以提高开发体验。

## What Changes
- 合并 `*ForTarget` 重复函数，统一函数签名
- 启用已有的 `ContentRenderer`、`StateManager` 公共模块
- 使用事件委托替代内联 `onclick` 属性
- 提取公共 CSS 到 `common.css`
- 添加 JSDoc 类型注释
- **无破坏性变更** - 所有功能保持完全一致

## Impact
- Affected specs: 前端所有页面
- Affected code: 
  - `static/index.html` - 主要重构
  - `static/browse.html` - 主要重构
  - `static/print.html` - CSS 提取
  - `static/js/*.js` - JSDoc 注释

## ADDED Requirements

### Requirement: 函数去重
系统 SHALL 统一 `*ForTarget` 函数与普通函数，通过默认参数区分场景。

#### Scenario: 统一函数签名
- **WHEN** 调用 `updateImageDisplay(index, display, target)` 
- **THEN** 若未指定 target，使用 currentTab 作为默认值

### Requirement: 公共模块使用
系统 SHALL 在 HTML 中使用已创建的 `ContentRenderer` 模块进行内容渲染。

#### Scenario: 使用 ContentRenderer
- **WHEN** 渲染内容列表
- **THEN** 调用 `ContentRenderer.renderContentList()` 而非内联代码

### Requirement: 事件委托
系统 SHALL 使用事件委托处理动态元素的点击事件。

#### Scenario: 删除按钮点击
- **WHEN** 用户点击删除按钮
- **THEN** 通过事件委托捕获并处理

### Requirement: 公共 CSS
系统 SHALL 提取三个 HTML 文件的公共 CSS 到 `common.css`。

#### Scenario: CSS 加载
- **WHEN** 页面加载
- **THEN** 先加载 `common.css`，再加载页面特定 CSS

### Requirement: JSDoc 类型注释
系统 SHALL 为公共 JS 模块添加 JSDoc 类型注释。

#### Scenario: IDE 类型提示
- **WHEN** 开发者编写代码
- **THEN** IDE 能够提供类型提示和参数信息

## MODIFIED Requirements
无

## REMOVED Requirements
无
