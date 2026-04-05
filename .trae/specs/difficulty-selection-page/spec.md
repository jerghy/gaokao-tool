# 难点选择页面 Spec

## Why
用户需要一个专门的页面来筛选包含"难点"(Difficulties)的题目，并能够选择性地标记题目中的重点难点ID，便于后续针对特定难点进行练习或复习。

## What Changes
- 新增 `static/difficulty.html` 页面文件
- 新增后端 API 端点 `/api/questions-with-difficulties` 用于筛选包含难点的题目
- 新增后端 API 端点 `/api/questions/<id>/selected-difficulties` 用于保存选择的难点ID列表
- 题目 JSON 数据结构新增 `selected_difficulty_ids` 字段

## Impact
- Affected specs: 无
- Affected code: 
  - `app.py` (新增 API 端点)
  - `static/difficulty.html` (新文件)

## ADDED Requirements

### Requirement: 难点题目筛选页面
系统应提供一个独立的难点选择页面，用于筛选和管理包含难点的题目。

#### Scenario: 访问难点选择页面
- **WHEN** 用户访问 `/difficulty` 路由
- **THEN** 系统显示难点选择页面，左侧显示包含难点的题目列表

#### Scenario: 筛选包含难点的题目
- **WHEN** 页面加载时
- **THEN** 系统自动筛选 `chemistry_preprocessing.Difficulties` 数组非空的题目
- **AND** 左侧列表显示这些题目的基本信息（ID、预览文本、标签）

#### Scenario: 查看题目难点详情
- **WHEN** 用户点击左侧列表中的某个题目
- **THEN** 右侧区域显示该题目的所有难点卡片
- **AND** 每个难点卡片显示：难度名称、难度等级、考点标签、适配分数段、突破价值
- **AND** 每个卡片右侧有一个多选框

#### Scenario: 选择难点并保存
- **WHEN** 用户勾选若干难点卡片的多选框
- **AND** 用户点击"保存"按钮
- **THEN** 系统将选择的难点ID列表保存到题目JSON的 `selected_difficulty_ids` 字段
- **AND** 显示保存成功提示

#### Scenario: 加载已选择的难点
- **WHEN** 用户选择一个已有 `selected_difficulty_ids` 字段的题目
- **THEN** 系统自动勾选对应的难点卡片

### Requirement: 后端 API 支持

#### Scenario: 获取包含难点的题目列表
- **WHEN** 前端请求 `GET /api/questions-with-difficulties`
- **THEN** 系统返回所有 `chemistry_preprocessing.Difficulties` 非空的题目列表
- **AND** 返回数据包含题目ID、创建时间、题目预览、标签、难点数量

#### Scenario: 保存选择的难点ID
- **WHEN** 前端请求 `PUT /api/questions/<id>/selected-difficulties`
- **AND** 请求体包含 `{"selected_difficulty_ids": [1, 2, 3]}`
- **THEN** 系统更新题目JSON文件，添加或更新 `selected_difficulty_ids` 字段
- **AND** 返回成功响应

## Data Structure

### 题目 JSON 新增字段
```json
{
  "selected_difficulty_ids": [1, 2, 3]
}
```

### 难点数据结构（已存在）
```json
{
  "chemistry_preprocessing": {
    "Difficulties": [
      {
        "DifficultyID": 1,
        "DifficultyName": "难点名称",
        "DifficultyLevel": 4,
        "ExamTag": "考点标签",
        "AdaptScore": "高分段≥80分",
        "BreakthroughValue": 5,
        "ProcessPriority": "最高",
        "QuestionAnchor": "题目锚点描述",
        "BreakthroughSolution": "突破方案..."
      }
    ]
  }
}
```
