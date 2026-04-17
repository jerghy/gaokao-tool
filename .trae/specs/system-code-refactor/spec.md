# 错题收录系统代码重构 Spec

## Why
当前系统经过多次功能迭代，后端 `app.py` 已膨胀至 900 行，所有路由、业务逻辑、数据访问混杂在一起；前端 HTML 页面巨大（browse.html 3037 行、print.html 2465 行、index.html 2052 行），内联 JS/CSS 难以维护；后端模块间职责边界模糊，`process_image_items`/`expand_image_items` 等核心业务逻辑散落在路由函数中。需要系统性重构以提升可维护性、可测试性和代码质量。

## What Changes
- 后端：将 app.py 拆分为路由层（Blueprint）、服务层、数据访问层，引入清晰的分层架构
- 后端：提取图片处理、截图管理、题目管理等业务逻辑到独立 Service 类
- 后端：消除全局状态（`pending_screenshots`、`tag_system` 等），改为应用上下文管理
- 前端：将巨型 HTML 页面中的内联 JS 提取为独立模块，按功能域拆分
- 前端：提取公共 CSS 为独立样式文件，消除跨页面重复样式
- 后端：统一数据访问模式，所有文件 I/O 通过 Repository 层操作

## Impact
- Affected specs: 无破坏性变更，所有现有功能保持兼容
- Affected code: app.py, tag_system.py, search_engine.py, image_manager.py, errors.py, 所有 HTML 页面, 所有 JS 模块

## ADDED Requirements

### Requirement: 后端分层架构
系统 SHALL 采用三层架构：路由层（Routes）、服务层（Services）、数据访问层（Repositories），各层职责清晰分离。

#### Scenario: 路由层只处理 HTTP 协议相关逻辑
- **WHEN** 一个 API 请求到达路由函数
- **THEN** 路由函数仅负责参数提取、调用 Service、格式化响应，不包含业务逻辑

#### Scenario: 服务层封装业务逻辑
- **WHEN** 需要执行题目保存、图片处理等业务操作
- **THEN** 由 Service 类统一协调 Repository 和外部依赖，路由层不直接操作 Repository

#### Scenario: 数据访问层封装存储细节
- **WHEN** 需要读写题目数据、标签数据
- **THEN** 通过 Repository 接口操作，调用方不感知底层是文件系统还是数据库

### Requirement: 后端模块拆分
系统 SHALL 将 app.py 拆分为多个 Blueprint 模块，按功能域组织路由。

#### Scenario: 题目相关路由独立
- **WHEN** 访问 `/api/questions`、`/api/save` 等题目 API
- **THEN** 由 `routes/question_routes.py` 中的 Blueprint 处理

#### Scenario: 图片相关路由独立
- **WHEN** 访问 `/api/upload-image`、`/api/split-image` 等图片 API
- **THEN** 由 `routes/image_routes.py` 中的 Blueprint 处理

#### Scenario: 截图相关路由独立
- **WHEN** 访问 `/api/screenshot/*` 等截图 API
- **THEN** 由 `routes/screenshot_routes.py` 中的 Blueprint 处理

#### Scenario: 标签相关路由独立
- **WHEN** 访问 `/api/tags`、`/api/questions/batch-add-tag` 等标签 API
- **THEN** 由 `routes/tag_routes.py` 中的 Blueprint 处理

### Requirement: 服务层提取
系统 SHALL 将核心业务逻辑提取为独立的 Service 类。

#### Scenario: QuestionService 封装题目管理逻辑
- **WHEN** 保存或更新题目
- **THEN** QuestionService 统一处理图片项处理（process_image_items）、标签同步、搜索索引刷新

#### Scenario: ImageService 封装图片处理逻辑
- **WHEN** 上传、分割或查询图片
- **THEN** ImageService 统一协调 ImageManager 和文件系统操作

#### Scenario: ScreenshotService 封装截图管理逻辑
- **WHEN** 上传、检查或消费截图
- **THEN** ScreenshotService 管理截图生命周期，包括过期清理

### Requirement: 数据访问层封装
系统 SHALL 将文件系统操作封装为 Repository 类。

#### Scenario: QuestionRepository 封装题目文件操作
- **WHEN** 需要读取、写入或删除题目 JSON 文件
- **THEN** 通过 QuestionRepository 操作，不直接使用 `os.listdir`/`json.load`/`json.dump`

#### Scenario: TagRepository 封装标签数据操作
- **WHEN** 需要操作标签数据
- **THEN** 通过 TagRepository 操作，TagSystem 成为 Repository 的实现

### Requirement: 消除全局状态
系统 SHALL 消除模块级全局变量，改为 Flask 应用上下文管理。

#### Scenario: 服务实例通过应用上下文获取
- **WHEN** 路由函数需要访问 Service
- **THEN** 通过 `current_app` 或依赖注入获取，而非直接引用全局变量

#### Scenario: 截图状态不再使用全局字典
- **WHEN** 操作待处理截图
- **THEN** 通过 ScreenshotService 的实例属性管理，而非模块级 `pending_screenshots` 字典

### Requirement: 前端 JS 模块拆分
系统 SHALL 将 HTML 页面中的内联 JavaScript 提取为独立模块文件。

#### Scenario: browse.html 内联 JS 提取
- **WHEN** 浏览页面加载
- **THEN** 页面引用独立的 `browse.js` 文件，HTML 中仅保留初始化调用

#### Scenario: index.html 内联 JS 提取
- **WHEN** 录入页面加载
- **THEN** 页面引用独立的 `index.js` 文件，HTML 中仅保留初始化调用

#### Scenario: print.html 内联 JS 提取
- **WHEN** 打印页面加载
- **THEN** 页面引用独立的 `print.js` 文件，HTML 中仅保留初始化调用

### Requirement: 前端公共样式提取
系统 SHALL 将跨页面重复的 CSS 提取为公共样式文件。

#### Scenario: 公共样式独立文件
- **WHEN** 多个页面使用相同的 CSS 规则
- **THEN** 这些规则定义在 `static/css/common.css` 中，各页面通过 `<link>` 引用

### Requirement: 后端配置集中管理
系统 SHALL 将所有配置项集中到配置模块。

#### Scenario: 路径配置集中管理
- **WHEN** 需要访问数据目录、图片目录等路径
- **THEN** 通过 `config.py` 中的配置对象获取，而非在各模块中硬编码或重复计算

## MODIFIED Requirements

### Requirement: API 接口保持不变
所有现有 API 端点、请求/响应格式 SHALL 保持完全兼容，重构不改变外部行为。

## REMOVED Requirements
无移除的需求。
