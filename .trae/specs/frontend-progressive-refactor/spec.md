# 前端渐进式重构 Spec

## Why
当前前端代码使用原生 HTML/JS，存在大量重复代码（约40%），状态管理混乱，维护困难。需要通过渐进式重构提取公共模块，消除重复代码，提高可维护性，同时保持所有现有功能完全一致。

## What Changes
- 创建 `static/js/` 目录存放公共 JavaScript 模块
- 提取公共工具函数到 `utils.js`
- 提取 API 封装到 `api.js`
- 提取图片处理逻辑到 `image-handler.js`
- 提取内容渲染逻辑到 `content-renderer.js`
- 提取状态管理到 `state.js`
- 修改 `index.html`、`browse.html`、`print.html` 引用新模块
- **无破坏性变更** - 所有功能保持完全一致

## Impact
- Affected specs: 无
- Affected code:
  - `static/index.html` - 引用公共模块
  - `static/browse.html` - 引用公共模块
  - `static/print.html` - 引用公共模块
  - 新增 `static/js/utils.js`
  - 新增 `static/js/api.js`
  - 新增 `static/js/image-handler.js`
  - 新增 `static/js/content-renderer.js`
  - 新增 `static/js/state.js`

## ADDED Requirements

### Requirement: 公共工具模块
系统应提供公共工具函数模块 `utils.js`。

#### Scenario: 工具函数
- **WHEN** 前端代码需要工具函数
- **THEN** 可以从 `utils.js` 导入以下函数：
  - `escapeHtml(text)` - HTML 转义
  - `renderLatex(text)` - LaTeX 渲染
  - `processTextWithLatex(text)` - 处理 LaTeX 文本
  - `renderRichtext(fragments)` - 渲染富文本
  - `cleanImageItem(item)` - 清理图片项数据
  - `cleanItems(items)` - 清理 items 列表

### Requirement: API 封装模块
系统应提供 API 封装模块 `api.js`。

#### Scenario: API 调用
- **WHEN** 前端需要调用后端 API
- **THEN** 可以使用以下封装函数：
  - `api.uploadImage(base64)` - 上传图片
  - `api.saveQuestion(data)` - 保存题目
  - `api.getQuestions(params)` - 获取题目列表
  - `api.updateQuestion(id, data)` - 更新题目
  - `api.deleteQuestion(id)` - 删除题目
  - `api.getTags()` - 获取标签
  - `api.splitImage(data)` - 分割图片
  - `api.checkScreenshot()` - 检查截图
  - `api.consumeScreenshot(id)` - 消费截图

### Requirement: 图片处理模块
系统应提供图片处理模块 `image-handler.js`。

#### Scenario: 图片处理
- **WHEN** 前端需要处理图片
- **THEN** 可以使用以下函数：
  - `handleImagePaste(file, target, callbacks)` - 处理图片粘贴
  - `updateImageDisplay(index, display, items, setItems)` - 更新图片显示方式
  - `updateImageSize(index, dimension, value, items, setItems)` - 更新图片尺寸
  - `openCharBoxModal(config)` - 打开字框标注模态框
  - `confirmCharBox(config)` - 确认字框标注

### Requirement: 内容渲染模块
系统应提供内容渲染模块 `content-renderer.js`。

#### Scenario: 内容渲染
- **WHEN** 前端需要渲染内容列表
- **THEN** 可以使用以下函数：
  - `renderContentList(container, items, callbacks)` - 渲染内容列表
  - `renderPreview(container, items)` - 渲染预览
  - `renderTags(container, tags, callbacks)` - 渲染标签
  - `renderSubQuestions(container, subQuestions, callbacks)` - 渲染小问

### Requirement: 状态管理模块
系统应提供简单状态管理模块 `state.js`。

#### Scenario: 状态管理
- **WHEN** 前端需要管理状态
- **THEN** 可以使用 `Store` 类：
  - `store.getState()` - 获取状态
  - `store.setState(newState)` - 设置状态
  - `store.subscribe(listener)` - 订阅状态变化

### Requirement: 功能一致性
重构后所有功能必须与原来完全一致。

#### Scenario: 功能验证
- **WHEN** 用户使用重构后的系统
- **THEN** 以下功能正常工作：
  - 题目录入（文本、图片、富文本）
  - 图片上传和显示
  - 图片字框标注
  - 图片分割线
  - 标签管理
  - 小问管理
  - 题目浏览
  - 题目编辑
  - 题目打印
  - 截图功能
  - 搜索功能

## MODIFIED Requirements
无

## REMOVED Requirements
无
