# 统一错误处理计划

## 目标
创建统一的错误处理机制，提高代码可维护性和一致性。

## 当前问题

1. **错误处理分散** - 17个 try-except 块，27处错误返回
2. **错误格式不统一** - 有的返回 `{'error': ...}`，有的直接抛异常
3. **HTTP状态码不一致** - 同类错误可能返回不同状态码
4. **缺少日志记录** - 错误发生时没有记录日志
5. **错误信息暴露内部细节** - 直接返回 `str(e)` 可能泄露敏感信息

## 实现方案

### 步骤1: 创建错误处理模块 `errors.py`

创建自定义异常类：
- `AppError` - 基础异常类
- `ValidationError` - 验证错误 (400)
- `NotFoundError` - 资源未找到 (404)
- `ConflictError` - 资源冲突 (409)
- `InternalError` - 内部错误 (500)

### 步骤2: 创建统一错误响应格式

```python
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "用户友好的错误信息",
        "details": {}  # 可选的详细信息
    }
}
```

### 步骤3: 在 `app.py` 中注册全局错误处理器

- 处理 `AppError` 及其子类
- 处理通用 `Exception`
- 处理 404 和 405 错误

### 步骤4: 重构现有 API 错误处理

逐个修改 API 端点，使用新的异常类替代直接返回错误。

## 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `errors.py` | 新建 | 错误处理模块 |
| `app.py` | 修改 | 注册错误处理器，重构API错误处理 |

## 详细实现

### errors.py 内容

```python
from typing import Optional, Dict, Any

class AppError(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        result = {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result

class ValidationError(AppError):
    """验证错误"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class NotFoundError(AppError):
    """资源未找到"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )

class ConflictError(AppError):
    """资源冲突"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )
```

### app.py 错误处理器

```python
from flask import jsonify
from errors import AppError
import logging

logger = logging.getLogger(__name__)

@app.errorhandler(AppError)
def handle_app_error(error: AppError):
    """处理应用自定义异常"""
    logger.warning(f"AppError: {error.code} - {error.message}")
    return jsonify(error.to_dict()), error.status_code

@app.errorhandler(404)
def handle_not_found(error):
    """处理404错误"""
    return jsonify({
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "请求的资源不存在"
        }
    }), 404

@app.errorhandler(405)
def handle_method_not_allowed(error):
    """处理405错误"""
    return jsonify({
        "success": False,
        "error": {
            "code": "METHOD_NOT_ALLOWED",
            "message": "不支持的请求方法"
        }
    }), 405

@app.errorhandler(Exception)
def handle_generic_error(error: Exception):
    """处理未捕获的异常"""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误"
        }
    }), 500
```

### API 重构示例

**修改前:**
```python
@app.route('/api/questions/<id>', methods=['DELETE'])
def delete_question(id):
    try:
        filepath = os.path.join(DATA_DIR, f"{id}.json")
        if not os.path.exists(filepath):
            return jsonify({'error': 'Question not found'}), 404
        
        # ... 删除逻辑
        
        return jsonify({'success': True, 'id': id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**修改后:**
```python
@app.route('/api/questions/<id>', methods=['DELETE'])
def delete_question(id):
    filepath = os.path.join(DATA_DIR, f"{id}.json")
    if not os.path.exists(filepath):
        raise NotFoundError("Question", id)
    
    # ... 删除逻辑
    
    return jsonify({'success': True, 'id': id})
```

## 任务列表

1. [x] 创建 `errors.py` 错误处理模块
2. [x] 在 `app.py` 中注册全局错误处理器
3. [x] 重构 `/api/upload-image` 错误处理
4. [x] 重构 `/api/save` 错误处理
5. [x] 重构 `/api/questions` 相关API错误处理
6. [x] 重构 `/api/tags` 相关API错误处理
7. [x] 重构 `/api/screenshot` 相关API错误处理
8. [x] 重构 `/api/split-image` 相关API错误处理
9. [x] 重构 `/api/images` 相关API错误处理
10. [x] 测试所有API错误响应

## 预期效果

- 错误响应格式统一
- HTTP状态码使用规范
- 错误信息对用户友好
- 内部错误不暴露敏感信息
- 便于日志记录和监控
