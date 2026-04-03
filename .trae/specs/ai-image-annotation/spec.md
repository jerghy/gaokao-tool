# AI图片标注功能 Spec

## Why
用户需要为 `images.json` 中未标记的图片配置自动生成 charBox（字框）和 splitLines（分割线）标注。通过AI视觉能力自动识别图片中的字符位置和分割线位置，减少手动标注工作量。

## What Changes
- 新增 `ai/image_annotator.py` 图片标注模块
- 实现基于AI视觉的 charBox 自动标注功能
- 实现基于AI视觉的 splitLines 自动标注功能
- 支持多线程批处理，输出进度
- 已标注的配置自动跳过

## Impact
- Affected specs: 图片标注系统
- Affected code: 
  - `ai/image_annotator.py` - 新增图片标注模块
  - `ai/__init__.py` - 导出新模块

## ADDED Requirements

### Requirement: 图片标注模块
系统应提供图片标注模块，能够自动为未标记的图片配置生成 charBox 和 splitLines。

#### Scenario: 标注未标记图片
- **WHEN** 用户运行图片标注脚本
- **THEN** 系统扫描 images.json 中所有 configs
- **AND** 识别没有 charBox 字段的配置
- **AND** 对每个未标记配置调用AI进行标注

### Requirement: charBox 自动标注
系统应通过AI视觉能力自动识别图片中适合作为字框的位置和大小。

#### Scenario: AI识别字框
- **WHEN** AI分析图片
- **THEN** AI识别图片中字体大小约12-14pt的最小单个字
- **AND** 返回字框的坐标信息（x, y, size）
- **AND** 如果AI返回非正方形，通过高宽平均计算正方形边长
- **AND** 坐标为相对于图片的比例值（0-1）

#### Scenario: charBox数据格式
- **WHEN** AI返回字框标注结果
- **THEN** 数据格式为：
  ```json
  {
    "charBox": {
      "x": 0.5,
      "y": 0.3,
      "size": 0.04,
      "fontSize": "medium"
    }
  }
  ```

### Requirement: splitLines 自动标注
系统应通过AI视觉能力自动识别图片中适合作为分割线的位置。

#### Scenario: AI识别分割线
- **WHEN** AI分析图片
- **THEN** AI识别图片中文字段落之间的间隔位置
- **AND** 返回分割线的Y坐标数组
- **AND** 坐标为相对于图片高度的比例值（0-1）

#### Scenario: splitLines数据格式
- **WHEN** AI返回分割线标注结果
- **THEN** 数据格式为：
  ```json
  {
    "splitLines": [0.35, 0.72]
  }
  ```

### Requirement: 多线程批处理
系统应支持多线程处理多个图片标注任务。

#### Scenario: 并发处理
- **WHEN** 存在多个未标记的图片配置
- **THEN** 系统使用线程池并发处理
- **AND** 输出处理进度（如：[3/85] 处理中...）
- **AND** 支持配置并发数

### Requirement: 跳过已标注
系统应自动跳过已有 charBox 标注的配置。

#### Scenario: 跳过已标注配置
- **WHEN** 配置已有 charBox 字段
- **THEN** 系统跳过该配置
- **AND** 在进度输出中标记为"已跳过"

### Requirement: AI配置
系统应使用指定的AI模型配置。

#### Scenario: AI模型配置
- **WHEN** 调用AI进行标注
- **THEN** 使用模型 "doubao-seed-2-0-mini-260215"
- **AND** reasoning_effort 设置为 "minimal"
- **AND** 输出格式为 JSON

### Requirement: 结果保存
系统应将标注结果保存回 images.json。

#### Scenario: 保存标注结果
- **WHEN** AI完成标注
- **THEN** 系统将 charBox 和 splitLines 写入对应配置
- **AND** 保持 images.json 的原有结构
- **AND** 保存后输出成功信息
