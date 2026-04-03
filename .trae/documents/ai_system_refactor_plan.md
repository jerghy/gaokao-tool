# AI 系统代码整理计划

## 当前状态分析

### 文件结构
```
ai/
├── __init__.py              # 统一导出
├── base.py                  # 公共基础模块 ✅
├── loader.py                # 数据加载
├── preprocessor.py          # 题目预处理
├── evaluator.py             # 质量评估
├── neural_reaction.py       # 神经反应
├── thinking_processor.py    # 思考过程
├── immersion_processor.py   # 沉浸式思考
├── generic_processor.py     # 通用处理器
├── batch_processor.py       # 批量处理（旧，仅用于 neural_reaction）
└── *_prompt.py              # 提示词文件
```

### 发现的问题

1. **重复的工具函数**
   - `parse_items_text()` 在 `immersion_processor.py` 和 `generic_processor.py` 中重复定义
   
2. **冗余文件**
   - `batch_processor.py` 功能已被 `generic_processor.py` 覆盖，仅用于 `neural_reaction`

3. **不必要的导入**
   - `preprocessor.py` 导入了 `extract_response_text` 但未使用

4. **命名不一致**
   - 有的用 `generate_xxx`，有的用 `xxx_and_save`

---

## 整理步骤

### 步骤 1：将工具函数移到 base.py
- 将 `parse_items_text()` 移到 `base.py`
- 更新 `immersion_processor.py` 和 `generic_processor.py` 的导入

### 步骤 2：删除冗余文件
- 删除 `batch_processor.py`（功能已被 `generic_processor.py` 覆盖）
- 更新 `__init__.py` 移除相关导出

### 步骤 3：清理不必要的导入
- 移除 `preprocessor.py` 中未使用的 `extract_response_text` 导入

### 步骤 4：验证所有模块正常工作
- 运行导入测试
- 确保所有功能正常

---

## 预期结果

整理后的结构：
```
ai/
├── __init__.py              # 统一导出
├── base.py                  # 公共基础模块（含工具函数）
├── loader.py                # 数据加载
├── preprocessor.py          # 题目预处理
├── evaluator.py             # 质量评估
├── neural_reaction.py       # 神经反应
├── thinking_processor.py    # 思考过程
├── immersion_processor.py   # 沉浸式思考
├── generic_processor.py     # 通用处理器
└── *_prompt.py              # 提示词文件
```

代码更简洁，无重复，易于扩展新的 AI 工作流。
