# PDF截图传输功能 Spec

## Why
用户在录入错题时，经常需要从PDF文件中截取题目图片。目前需要手动截图、保存、再粘贴，操作繁琐。通过在PDF查看器中直接截图并传输到错题收录页面，可以大幅提升效率。

## What Changes
- 在 `pdfjs/web/viewer.html` 上添加截图功能，支持鼠标拖拽选择区域
- 在错题收录页面 (`index.html`) 和 PDF截图页面 (`viewer.html`) 都添加端口号输入框
- 实现基于 WebSocket 的跨页面图片传输
- 右键菜单发送截图功能，发送前验证端口连接状态
- 错题收录页面接收图片后，模拟粘贴行为添加到内容区域

## Impact
- Affected specs: 错题收录系统
- Affected code: 
  - `static/index.html` - 添加端口输入框和WebSocket接收逻辑
  - `pdfjs/web/viewer.html` - 添加截图功能、端口输入框和WebSocket发送逻辑
  - `pdfjs/web/viewer.css` - 添加截图相关样式

## ADDED Requirements

### Requirement: PDF截图功能
系统 SHALL 在PDF查看器页面提供截图功能，允许用户通过鼠标拖拽选择截图区域。

#### Scenario: 选择截图区域
- **WHEN** 用户在PDF页面上按住鼠标左键并拖拽
- **THEN** 显示一个半透明矩形框标识选择区域
- **AND** 用户可以多次重新选择区域（右键未点击前）

#### Scenario: 取消截图区域
- **WHEN** 用户按下 Escape 键或点击其他位置
- **THEN** 清除当前选择的截图区域

### Requirement: 端口连接功能
系统 SHALL 提供端口输入框，允许用户配置WebSocket通信端口。

#### Scenario: 输入端口号
- **WHEN** 用户在端口输入框中输入端口号
- **THEN** 系统保存该端口号用于WebSocket连接

#### Scenario: 连接状态显示
- **WHEN** 用户点击连接按钮
- **THEN** 系统尝试建立WebSocket连接
- **AND** 显示连接成功或失败状态

### Requirement: 截图发送功能
系统 SHALL 提供右键菜单发送截图功能。

#### Scenario: 发送截图
- **WHEN** 用户已选择截图区域
- **AND** 用户右键点击并选择"发送截图"
- **AND** WebSocket连接已建立
- **THEN** 将截图区域转换为Base64图片数据
- **AND** 通过WebSocket发送到错题收录页面

#### Scenario: 发送失败提示
- **WHEN** 用户尝试发送截图但WebSocket未连接
- **THEN** 显示"请先连接端口"提示
- **AND** 不执行发送操作

### Requirement: 图片接收功能
系统 SHALL 在错题收录页面接收并处理传输的图片。

#### Scenario: 接收图片
- **WHEN** 错题收录页面收到WebSocket传输的图片数据
- **THEN** 将图片添加到当前激活的内容区域（原题或答案）
- **AND** 图片处理方式与用户粘贴图片一致（上传到服务器、显示预览）

#### Scenario: 自动保存图片
- **WHEN** 收到图片数据
- **THEN** 调用 `/api/upload-image` 接口保存图片
- **AND** 在预览区显示图片

## MODIFIED Requirements
无

## REMOVED Requirements
无
