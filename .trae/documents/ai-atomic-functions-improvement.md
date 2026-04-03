# AI 原子化函数改进计划

## 问题分析

### 1. `parallel_map` 异常处理问题
当前实现：异常时把异常对象放到结果列表中
```python
# 当前行为
results = parallel_map(lambda x: 1/x, [1, 0, 2])
# 返回: [1, ZeroDivisionError, 2]  # 混杂异常对象！
```

问题：`call_ai_batch_texts` 返回 `list[str]`，但实际可能包含异常对象

### 2. 缺少错误信息
批量处理时，不知道哪个项目失败了

### 3. 缺少进度显示
批量处理时没有默认的进度输出

## 改进方案

### 1. 添加 `parallel_map_safe` 函数
返回结构化结果，包含成功/失败信息

### 2. 添加 `BatchResult` 数据类
统一批量处理结果格式

### 3. 修改 `call_ai_batch_texts` 
使用安全版本，返回详细结果

## 实现步骤

### Step 1: 添加 `BatchResult` 数据类
```python
@dataclass
class BatchResult(Generic[R]):
    index: int
    success: bool
    result: Optional[R]
    error: Optional[str]
```

### Step 2: 添加 `parallel_map_safe` 函数
```python
def parallel_map_safe(
    func: Callable[[T], R],
    items: list[T],
    max_workers: int = 3,
    on_progress: Optional[Callable[[int, int, BatchResult], None]] = None,
) -> list[BatchResult[R]]:
    ...
```

### Step 3: 修改 `call_ai_batch_texts`
使用 `parallel_map_safe`，返回 `list[BatchResult[str]]`

### Step 4: 更新 `__init__.py` 导出
添加 `BatchResult`, `parallel_map_safe`

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `ai/base.py` | 添加 `BatchResult`, `parallel_map_safe`，修改 `call_ai_batch_texts` |
| `ai/__init__.py` | 导出新函数 |
