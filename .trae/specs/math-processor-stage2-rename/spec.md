# 数学处理器 Stage2 函数重命名与适配 Spec

## Why
用户更新了 AI 提示词文件内容，Stage 2 的功能从"生成完整思维链"升级为"生成深度思维引导式训练内容"，需要适配代码以反映这一变化。

## What Changes
- 将 `deep_parse_thinking()` 函数重命名为 `generate_guided_training()`
- 更新 `__all__` 导出列表
- 更新函数文档字符串以反映新的功能定位
- AI 配置保持 `reasoning_effort=medium` 不变
- 提示词文件名保持不变（内容已由用户更新）

## Impact
- Affected code: `ai/math_processor.py`
- 提示词文件: `ai/tsc/Math_Thinking_Chain_Deep_Parse_Prompt.txt`（内容已更新）

## MODIFIED Requirements

### Requirement: Stage 2 处理函数
函数名从 `deep_parse_thinking()` 改为 `generate_guided_training()`，功能定位从"思维链深度拆解"升级为"深度思维引导式训练生成"。

#### Scenario: 思维提升类题目处理
- **WHEN** `classify_result == "思维提升类"`
- **THEN** 调用 `generate_guided_training()` 生成深度思维引导式训练内容
- **AND** 输出包含6个环节的问题+三层标准答案+最终结论校验+教练提示
