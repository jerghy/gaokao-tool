# 字符标记功能重构 Spec

## Why
当前 AI 标注存在坐标转换错误：AI 返回的是归一化到 1000x1000 的比例坐标（取值范围 [0, 999]），但代码错误地将其当作像素坐标处理。需要重构整个字符标记功能，确保 AI 标注和人工标注都能正确工作，最终实现图片自动缩放。

## What Changes
- **BREAKING**: 修改 AI 坐标解析逻辑，正确处理 1000x1000 归一化坐标
- 重构 CharBox 数据结构，明确字段含义
- 统一 AI 标注和人工标注的数据格式
- 修改 browse.html 和 print.html 的字框显示和缩放计算逻辑

## Impact
- Affected specs: image-char-box-annotation
- Affected code:
  - `ai/image_annotator.py` - AI 标注解析
  - `static/browse.html` - 字框显示和手动标注
  - `static/print.html` - 图片缩放计算

## ADDED Requirements

### Requirement: AI 坐标正确解析
系统 SHALL 正确解析 AI 返回的 1000x1000 归一化坐标。

#### Scenario: AI 返回 bbox 坐标
- **GIVEN** AI 返回 `<bbox>x1 y1 x2 y2</bbox>` 格式
- **WHEN** x1, y1, x2, y2 是归一化到 1000x1000 的坐标（范围 [0, 999]）
- **THEN** 系统将坐标除以 1000 得到真正的比例值（范围 [0, 1]）

### Requirement: CharBox 数据结构
系统 SHALL 使用明确的 CharBox 数据结构存储字框信息。

#### 字段定义
- `x`: 左上角 x 比例坐标（0-1）
- `y`: 左上角 y 比例坐标（0-1）
- `size`: 字框尺寸比例（基于图片宽度，0-1）
- `fontSize`: 字体大小类别（large/medium/small）

### Requirement: 图片自动缩放
系统 SHALL 根据 charBox 正确计算图片缩放比例。

#### Scenario: 有 charBox 的图片
- **GIVEN** 图片配置包含 charBox
- **WHEN** 渲染图片
- **THEN** 根据 charBox.size 和目标字体大小计算缩放比例
- **AND** 图片正确缩放使得字框中的字达到目标字体大小

## MODIFIED Requirements

### Requirement: AI 标注提示词
AI 标注提示词 SHALL 返回正确的 bbox 格式。

当前提示词：
```
帮我框选图片中随机一个字的范围（如果没有字就框一个你认为12pt的字框），以<bbox>x1 y1 x2 y2</bbox>的形式表示，仅输出：<bbox>x1 y1 x2 y2</bbox>
```

## REMOVED Requirements
无
