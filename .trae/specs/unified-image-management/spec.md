# 统一图片管理系统 Spec

## Why
当前图片的元数据（路径、显示方式、尺寸、字框标注、分割线）分散存储在各个题目的JSON中，导致：
1. 同一张图片被多个题目引用时，数据重复存储
2. 图片管理困难，无法统一查看和管理所有图片
3. 修改图片属性时需要遍历所有题目
4. 无法追踪图片的使用情况

通过创建统一的图片管理系统，可以解决上述问题，同时保持现有的字框标注、分割线等功能。

## What Changes
- 创建统一的图片管理文件 `images.json`
- 图片元数据集中存储，包括：路径、显示方式、尺寸、字框标注、分割线
- 题目JSON中的图片项改为引用图片ID
- 新增图片管理API接口
- 修改前端图片上传和显示逻辑
- **BREAKING** 数据格式变更，需要迁移现有数据

## Impact
- Affected specs: 
  - image-char-box-annotation（字框标注功能保持不变）
  - image-split-lines（分割线功能保持不变）
- Affected code:
  - `app.py` - 新增图片管理API，修改题目保存/读取逻辑
  - `static/index.html` - 修改图片上传和引用逻辑
  - `static/browse.html` - 修改图片显示逻辑
  - `static/print.html` - 修改打印时的图片处理
  - 新增 `image_manager.py` - 图片管理模块

## ADDED Requirements

### Requirement: 图片数据统一存储
系统应将所有图片的元数据统一存储在 `images.json` 文件中。

#### Scenario: 图片数据结构
- **WHEN** 系统存储图片元数据
- **THEN** `images.json` 包含以下结构：
```json
{
  "images": {
    "img_001": {
      "id": "img_001",
      "filename": "20260321124838_90d2e800.png",
      "path": "img/20260321124838_90d2e800.png",
      "created_at": "2026-03-21 12:48:38",
      "width": 800,
      "height": 600,
      "file_size": 12345
    }
  }
}
```

### Requirement: 图片使用配置存储
系统应将图片的使用配置（显示方式、尺寸、字框、分割线）存储在 `images.json` 中，与图片元数据关联。

#### Scenario: 图片配置数据结构
- **WHEN** 用户为图片设置显示配置
- **THEN** 配置存储在 `images.json` 的 `configs` 字段中：
```json
{
  "configs": {
    "cfg_001": {
      "id": "cfg_001",
      "image_id": "img_001",
      "display": "center",
      "width": 450,
      "height": "auto",
      "charBox": {
        "fontSize": "medium",
        "size": 0.033,
        "x": 0.51,
        "y": 0.035
      },
      "splitLines": [0.3, 0.6]
    }
  }
}
```

### Requirement: 题目引用图片配置
题目JSON中的图片项应引用图片配置ID，而非存储完整配置。

#### Scenario: 题目图片引用
- **WHEN** 题目包含图片
- **THEN** 题目JSON中的图片项结构为：
```json
{
  "type": "image",
  "config_id": "cfg_001"
}
```

### Requirement: 图片管理API
系统应提供图片管理的API接口。

#### Scenario: 上传图片
- **WHEN** 用户上传图片
- **THEN** 系统生成唯一图片ID
- **AND** 保存图片文件到 `img/` 目录
- **AND** 在 `images.json` 中创建图片记录
- **AND** 返回图片ID

#### Scenario: 创建图片配置
- **WHEN** 用户在题目中使用图片
- **THEN** 系统创建图片配置记录
- **AND** 返回配置ID
- **AND** 配置与图片ID关联

#### Scenario: 更新图片配置
- **WHEN** 用户修改图片的显示方式、尺寸、字框或分割线
- **THEN** 系统更新对应的配置记录

#### Scenario: 删除图片配置
- **WHEN** 图片配置不再被任何题目使用
- **THEN** 系统可选择性删除该配置

#### Scenario: 获取图片信息
- **WHEN** 前端请求图片信息
- **THEN** 系统返回图片元数据和配置信息

### Requirement: 图片使用追踪
系统应追踪每个图片配置被哪些题目使用。

#### Scenario: 记录使用关系
- **WHEN** 题目引用图片配置
- **THEN** 配置记录中包含引用该配置的题目ID列表

### Requirement: 数据迁移
系统应提供数据迁移功能，将现有数据转换为新格式。

#### Scenario: 迁移现有数据
- **WHEN** 执行数据迁移
- **THEN** 遍历 `data/` 目录下所有题目JSON
- **AND** 提取所有图片项
- **AND** 为每个唯一图片创建图片记录
- **AND** 为每个图片使用创建配置记录
- **AND** 更新题目JSON中的图片引用

## MODIFIED Requirements

### Requirement: 图片上传接口（原 `/api/upload-image`）
系统应修改图片上传接口，返回图片ID而非路径。

#### Scenario: 上传图片响应
- **WHEN** 图片上传成功
- **THEN** 返回：
```json
{
  "success": true,
  "image_id": "img_001",
  "filename": "20260321124838_90d2e800.png"
}
```

### Requirement: 题目保存接口（原 `/api/save`）
系统应修改题目保存接口，处理图片配置的创建和更新。

#### Scenario: 保存题目时处理图片
- **WHEN** 保存包含图片的题目
- **THEN** 系统自动创建或更新图片配置
- **AND** 题目中存储配置ID引用

### Requirement: 题目读取接口（原 `/api/questions`）
系统应修改题目读取接口，返回完整的图片信息。

#### Scenario: 读取题目时展开图片
- **WHEN** 读取题目详情
- **THEN** 系统根据配置ID查找图片配置
- **AND** 根据图片ID查找图片元数据
- **AND** 返回合并后的完整图片信息

## REMOVED Requirements

无移除的需求。所有现有功能（字框标注、分割线）保持不变，仅改变存储方式。
