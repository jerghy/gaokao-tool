# AI 工作流重构计划：引入 AI 对象

## 问题分析

当前设计存在的问题：

1. **配置分散** - AI 相关配置分散在多处：
   - `AIContext` 创建时传入 `api_key`, `model`
   - `q.ai()` 调用时传入 `reasoning_effort`, `max_output_tokens`, `model` 等
   - 参数传递繁琐，容易遗漏

2. **缺乏统一抽象** - 没有一个"AI"的概念对象来封装所有 AI 配置

3. **难以复用配置** - 想要定义"快速模式"、"深度思考模式"等预设配置不方便

## 改进方案

### 核心设计：引入 `AI` 对象

创建一个 `AI` 类，封装所有 AI 调用相关的配置：

```python
from ai import AI, ReasoningEffort

# 预定义配置
fast_ai = AI(model="doubao-seed-2-0-pro-260215", reasoning_effort=ReasoningEffort.low)
think_ai = AI(model="doubao-seed-2-0-pro-260215", reasoning_effort=ReasoningEffort.high)

# 使用
ctx = AIContext(data_dir="data", ai=think_ai)
q = ctx.question("xxx")
q.ai("分析题目", ai=fast_ai)  # 临时使用快速模式
```

### 实现步骤

#### Step 1: 在 `base.py` 中创建 `AI` 类

```python
@dataclass
class AI:
    """AI 配置对象，封装模型和调用参数"""
    model: str = "doubao-seed-2-0-pro-260215"
    reasoning_effort: Union[ReasoningEffort, str] = ReasoningEffort.high
    max_output_tokens: int = 131072
    api_key: Optional[str] = None  # None 表示从环境变量读取
    timeout: int = 1800
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    # 预设模式
    @classmethod
    def fast(cls) -> "AI":
        """快速模式：低推理深度，适合简单任务"""
        return cls(reasoning_effort=ReasoningEffort.low, max_output_tokens=32768)
    
    @classmethod
    def think(cls) -> "AI":
        """思考模式：高推理深度，适合复杂分析"""
        return cls(reasoning_effort=ReasoningEffort.high, max_output_tokens=131072)
    
    @classmethod
    def deep(cls) -> "AI":
        """深度模式：最大推理深度和输出长度"""
        return cls(reasoning_effort=ReasoningEffort.high, max_output_tokens=262144)
    
    def to_config(self) -> AIConfig:
        """转换为 AIConfig（用于底层调用）"""
        return AIConfig(
            api_key=self.api_key or os.getenv("ARK_API_KEY", ""),
            model=self.model,
            max_output_tokens=self.max_output_tokens,
            reasoning_effort=self.reasoning_effort,
            timeout=self.timeout,
            base_url=self.base_url,
        )
```

#### Step 2: 修改 `AIContext` 接受 `AI` 对象

```python
class AIContext:
    def __init__(
        self,
        data_dir: str,
        ai: Optional[AI] = None,  # 新增：AI 对象
        api_base_url: str = "http://localhost:5000",
        # 以下参数保留用于向后兼容
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.data_dir = data_dir
        self.api_base_url = api_base_url
        
        # 优先使用 AI 对象
        if ai is not None:
            self._ai = ai
        else:
            # 向后兼容：从单独参数构建
            self._ai = AI(
                api_key=api_key,
                model=model or "doubao-seed-2-0-pro-260215",
            )
    
    @property
    def ai(self) -> AI:
        return self._ai
```

#### Step 3: 修改 `Question.ai()` 方法接受 `AI` 对象

```python
class Question:
    def ai(
        self,
        system_prompt: str,
        output_field: Optional[str] = None,
        ai: Optional[AI] = None,  # 新增：AI 对象
        context: Optional[str] = None,
        # 以下参数保留用于向后兼容（会覆盖 AI 对象中的对应配置）
        model: Optional[str] = None,
        reasoning_effort: Optional[Union[ReasoningEffort, str]] = None,
        max_output_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> str:
        # 获取基础 AI 配置
        base_ai = ai or (self._ctx.ai if self._ctx else AI())
        
        # 应用覆盖参数
        config = base_ai.to_config()
        if model:
            config.model = model
        if reasoning_effort:
            config.reasoning_effort = reasoning_effort
        if max_output_tokens:
            config.max_output_tokens = max_output_tokens
        if api_key:
            config.api_key = api_key
        
        # 调用 AI
        client = AIClient(config)
        # ... 其余逻辑不变
```

#### Step 4: 修改 `batch_ai` 函数

```python
def batch_ai(
    questions: list[Question],
    system_prompt: str,
    output_field: str = None,
    ai: Optional[AI] = None,  # 新增
    max_workers: int = 3,
    # 向后兼容参数
    **kwargs
) -> dict:
    # ...
```

#### Step 5: 更新导出和文档

- 在 `__init__.py` 中导出 `AI` 类
- 更新 `AI_WORKFLOW_GUIDE.md` 文档

## 使用示例

### 基本使用

```python
from ai import AIContext, AI, ReasoningEffort

# 方式一：使用默认 AI 配置
ctx = AIContext(data_dir="data")

# 方式二：传入自定义 AI 对象
ctx = AIContext(
    data_dir="data",
    ai=AI(reasoning_effort=ReasoningEffort.high, max_output_tokens=262144)
)

# 方式三：使用预设模式
ctx = AIContext(data_dir="data", ai=AI.think())
```

### 调用时切换 AI 配置

```python
from ai import AI, ReasoningEffort

q = ctx.question("xxx")

# 使用上下文默认 AI
q.ai("分析题目")

# 临时使用快速模式
q.ai("简单分类", ai=AI.fast())

# 临时使用深度模式
q.ai("深度分析", ai=AI.deep())

# 覆盖单个参数
q.ai("分析", reasoning_effort=ReasoningEffort.minimal)
```

### 预定义多个 AI 配置

```python
from ai import AI, ReasoningEffort

# 定义项目级 AI 配置
FAST_AI = AI(reasoning_effort=ReasoningEffort.low, max_output_tokens=32768)
THINK_AI = AI(reasoning_effort=ReasoningEffort.high, max_output_tokens=131072)
DEEP_AI = AI(reasoning_effort=ReasoningEffort.high, max_output_tokens=262144)

# 批量处理时使用
batch_ai(questions, "分析", ai=THINK_AI)
```

## 向后兼容性

所有现有代码无需修改即可继续工作：

```python
# 旧代码仍然有效
ctx = AIContext(data_dir="data", api_key="xxx", model="xxx")
q.ai("分析", reasoning_effort="high", max_output_tokens=65536)
```

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `ai/base.py` | 新增 `AI` 类，包含预设模式方法 |
| `ai/workflow.py` | 修改 `AIContext` 和 `Question.ai()` 接受 `AI` 对象 |
| `ai/__init__.py` | 导出 `AI` 类 |
| `AI_WORKFLOW_GUIDE.md` | 更新文档说明新的使用方式 |
