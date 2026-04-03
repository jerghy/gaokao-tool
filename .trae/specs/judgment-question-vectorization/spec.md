# 判断题向量化和AI合并功能 Spec

## Why

判断题数量庞大，存在大量相似或重复的题目。通过向量化可以计算题目相似度，找出相似题目，再由AI智能合并，减少冗余，提高题库质量。

## What Changes

* 新增判断题向量化模块，将题目文本转换为向量

* 向量保存到原JSON文件的每条记录中

* 新增相似度计算功能，找出相似度高于阈值的题目对

* 新增AI合并功能，将相似题目交由AI判断是否合并并生成合并结果

## Impact

* Affected code: `judgment_questions.py`, `judgment_questions.json`

* New module: `ai/question_vectorizer.py`

## ADDED Requirements

### Requirement: 判断题向量化

系统应能够将判断题的题目文本转换为向量表示。

#### Scenario: 向量化单个题目

* **WHEN** 用户调用向量化功能

* **THEN** 系统使用火山引擎嵌入API将题目文本转换为2048维向量

* **AND** 向量保存到对应题目的`embedding`字段

#### Scenario: 批量向量化

* **WHEN** JSON文件中有多个题目需要向量化

* **THEN** 系统批量处理所有未向量化的题目

* **AND** 跳过已有向量的题目

### Requirement: 相似度计算

系统应能够计算题目之间的相似度并找出相似题目对。

#### Scenario: 计算相似度

* **WHEN** 用户请求查找相似题目

* **THEN** 系统使用余弦相似度计算所有题目对之间的相似度

* **AND** 返回相似度高于阈值（默认0.85）的题目对列表

### Requirement: AI合并相似题目

系统应能够将相似题目交由AI判断并合并。

#### Scenario: AI合并

* **WHEN** 用户请求合并相似题目

* **THEN** 系统将相似题目对发送给AI

* **AND** AI判断是否应该合并

* **AND** 如果合并，AI生成合并后的题目和答案

* **AND** 合并结果保存到JSON

### Requirement: 增量保存

向量化结果应增量保存到JSON文件。

#### Scenario: 保存向量

* **WHEN** 向量化完成

* **THEN** 向量数据保存到原JSON文件对应记录的`embedding`字段

* **AND** 不影响其他字段数据

