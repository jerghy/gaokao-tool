# CharBox 数据结构重构 Spec

## Why
当前 CharBox 使用单一的 `size` 字段（取宽高最大值），但这丢失了 AI 输出的精确宽高信息。改为 `width` 和 `height` 两个字段可以更精确地适配 AI 输出，同时保留字框的完整尺寸信息。

## What Changes
- **BREAKING**: CharBox 数据结构从 `size` 改为 `width` + `height`
- 修改 AI 解析逻辑，直接保存宽高比例
- 修改 browse.html 手动标注逻辑，保存宽高
- 修改 print.html 图片缩放逻辑，使用 width 和 height 计算缩放

## Impact
- Affected specs: charbox-refactor-2024
- Affected code:
  - `ai/image_annotator.py` - CharBox 类和解析函数
  - `static/browse.html` - 字框显示和手动标注
  - `static/print.html` - 图片缩放计算

## ADDED Requirements

### Requirement: CharBox 数据结构
系统 SHALL 使用 width 和 height 字段存储字框尺寸。

#### 字段定义
- `x`: 左上角 x 比例坐标（0-1）
- `y`: 左上角 y 比例坐标（0-1）
- `width`: 字框宽度比例（基于图片宽度，0-1）
- `height`: 字框高度比例（基于图片高度，0-1）
- `fontSize`: 字体大小类别（large/medium/small）

### Requirement: AI 输出直接映射
系统 SHALL 直接将 AI 输出的宽高转换为比例值保存。

#### Scenario: AI 返回 bbox 坐标
- **GIVEN** AI 返回 `<bbox>x1 y1 x2 y2</bbox>` 格式
- **WHEN** 解析坐标
- **THEN** width = (x2 - x1) / 1000
- **AND** height = (y2 - y1) / 1000

### Requirement: 图片缩放计算
系统 SHALL 使用 width 和 height 计算图片缩放比例。

#### Scenario: 计算缩放比例
- **GIVEN** charBox 包含 width 和 height
- **WHEN** 计算缩放
- **THEN** 使用 max(width, height) 作为基准尺寸

## REMOVED Requirements

### Requirement: 单一 size 字段
**Reason**: 丢失精确宽高信息，不利于后续处理
**Migration**: 将现有 size 值同时赋给 width 和 height
