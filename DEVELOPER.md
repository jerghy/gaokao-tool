# 错题收录系统 - 开发者文档

> 本文档面向编程人员，详细说明系统的内部实现、架构设计和扩展开发指南。

---

## 目录

1. [技术栈](#1-技术栈)
2. [目录结构](#2-目录结构)
3. [系统架构](#3-系统架构)
4. [核心模块](#4-核心模块)
5. [数据结构](#5-数据结构)
6. [API接口](#6-api接口)
7. [前端开发](#7-前端开发)
8. [AI模块](#8-ai模块)
9. [扩展开发指南](#9-扩展开发指南)
10. [开发规范](#10-开发规范)

---

## 1. 技术栈

### 1.1 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要编程语言 |
| Flask | 2.x | Web框架 |
| Flask-CORS | - | 跨域支持 |
| Pillow | - | 图片处理 |
| volcengine-python-sdk | - | 火山引擎AI SDK |

### 1.2 前端

| 技术 | 用途 |
|------|------|
| 原生 JavaScript | 核心逻辑（无框架） |
| KaTeX | LaTeX公式渲染 |
| marked | Markdown解析 |
| PDF.js | PDF查看器 |

### 1.3 数据存储

| 文件 | 用途 |
|------|------|
| JSON文件 | 所有数据存储（无数据库） |
| 文件系统 | 图片存储 |

---

## 2. 目录结构

```
d:\space\html\print\
│
├── app.py                    # Flask主应用，API入口
├── image_manager.py          # 图片管理模块
├── tag_system.py             # 标签系统模块
├── search_engine.py          # 搜索引擎模块
├── migrate_images.py         # 数据迁移脚本
│
├── data/                     # 题目数据目录
│   ├── 20260321124856.json   # 单个题目文件
│   └── ...
│
├── img/                      # 图片存储目录
│   ├── 20260321124838_90d2e800.png
│   └── ...
│
├── screenshot_temp/          # 截图临时目录
├── split_cache/              # 图片分割缓存
│
├── images.json               # 图片元数据库
├── tags_data.json            # 标签数据库
├── pending_screenshots.json  # 待处理截图
│
├── static/                   # 前端静态文件
│   ├── index.html            # 录入页面
│   ├── browse.html           # 浏览页面
│   ├── print.html            # 打印页面
│   └── pdfjs/                # PDF查看器
│
├── ai/                       # AI分析模块
│   ├── __init__.py
│   ├── base.py               # AI基础类和工具函数
│   ├── preprocessor.py       # 题目预处理
│   ├── loader.py             # 数据加载器
│   ├── prompts.py            # 提示词模板
│   └── ...
│
└── .trae/                    # Trae配置目录
    └── specs/                # 功能规范文档
```

---

## 3. 系统架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   index.html    │   browse.html   │        print.html           │
│   (录入页面)     │   (浏览页面)     │        (打印页面)            │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API层 (Flask app.py)                       │
├─────────────────────────────────────────────────────────────────┤
│  /api/save  /api/questions  /api/upload-image  /api/tags  ...  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ImageManager   │  │   TagSystem     │  │  SearchEngine   │
│  (图片管理)      │  │   (标签系统)     │  │   (搜索引擎)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据层 (JSON Files)                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   images.json   │  tags_data.json │    data/*.json (题目)       │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### 3.2 数据流向

```
用户操作 → 前端页面 → API请求 → 后端处理 → JSON存储
                                    ↓
                              模块处理
                         ┌─────┼─────┐
                         ↓     ↓     ↓
                      Image  Tag  Search
                     Manager System Engine
```

### 3.3 系统启动流程

```python
# app.py 启动流程

1. 导入依赖模块
2. 初始化Flask应用
3. 定义目录路径 (BASE_DIR, IMG_DIR, DATA_DIR, etc.)
4. 初始化核心模块:
   - tag_system = TagSystem(data_path)
   - search_engine = SearchEngine(DATA_DIR)
   - image_manager = ImageManager(IMAGES_DATA_PATH)
5. 创建必要目录
6. 加载待处理截图
7. 从data目录初始化标签系统
8. 注册API路由
9. 启动Flask服务 (app.run())
```

---

## 4. 核心模块

### 4.1 app.py - 主应用模块

#### 职责
- 提供HTTP API接口
- 协调各模块工作
- 处理请求路由

#### 关键函数

##### process_image_items(items, question_id)
处理图片项，创建或更新图片配置。

```python
def process_image_items(items, question_id):
    """
    处理图片项列表，将图片信息存储到图片管理系统
    
    Args:
        items: 题目或答案的items列表
        question_id: 题目ID
    
    Returns:
        处理后的items列表，图片项只包含config_id
    
    处理逻辑:
        1. 如果item有config_id，更新配置
        2. 如果item有image_id，创建新配置
        3. 如果item只有src（旧格式），创建图片记录和配置
    """
```

##### expand_image_items(items)
展开图片项，返回完整信息供前端使用。

```python
def expand_image_items(items):
    """
    将存储格式（只有config_id）展开为前端需要的完整格式
    
    Args:
        items: 存储格式的items列表
    
    Returns:
        展开后的items列表，包含src, display, width, height, charBox, splitLines
    """
```

#### 注意事项
- 所有修改题目数据的API都需要调用`process_image_items`
- 所有返回题目数据的API都需要调用`expand_image_items`
- 使用`search_engine.refresh()`刷新搜索缓存

---

### 4.2 image_manager.py - 图片管理模块

#### 职责
- 统一管理所有图片的元数据
- 管理图片配置（显示方式、尺寸、字框、分割线）
- 追踪图片使用情况

#### 类设计

```python
class ImageManager:
    def __init__(self, data_path: str):
        """
        初始化图片管理器
        
        Args:
            data_path: images.json的路径
        """
    
    # 图片操作
    def add_image(filename, path, width, height, file_size) -> str
    def get_image(image_id: str) -> Optional[Dict]
    def get_image_by_filename(filename: str) -> Optional[Dict]
    
    # 配置操作
    def create_config(image_id, display, width, height, charBox, splitLines) -> str
    def get_config(config_id: str) -> Optional[Dict]
    def update_config(config_id: str, **kwargs) -> bool
    def delete_config(config_id: str) -> bool
    
    # 使用追踪
    def add_usage(config_id: str, question_id: str)
    def remove_usage(config_id: str, question_id: str)
    
    # 查询
    def get_full_image_info(config_id: str) -> Optional[Dict]
    def get_all_images() -> List[Dict]
    def get_all_configs() -> List[Dict]
```

#### ID生成规则

```
图片ID: img_YYYYMMDDHHMMSS_随机8位字母数字
配置ID: cfg_YYYYMMDDHHMMSS_随机8位字母数字

示例:
  img_20260321124838_90d2e800
  cfg_20260321124838_a1b2c3d4
```

#### 线程安全
使用`threading.RLock()`可重入锁保证线程安全：

```python
def add_image(self, ...):
    with self._lock:  # 所有操作都在锁保护下
        # ... 操作代码
        self._save_data()
```

---

### 4.3 tag_system.py - 标签系统模块

#### 职责
- 管理题目标签
- 构建层级标签树
- 支持布尔表达式搜索

#### 数据结构

```python
# tags_data.json 结构
{
    "records": {
        "20260321124856": ["数学", "代数::方程"],
        "20260321124857": ["英语", "语法"]
    },
    "tag_tree": {
        "数学": {
            "children": {
                "代数": {
                    "children": {
                        "方程": {}
                    }
                }
            }
        },
        "英语": {}
    }
}
```

#### 层级标签
使用`::`分隔层级：

```
数学::代数::方程
  └── 数学
       └── 代数
            └── 方程
```

#### 布尔搜索语法

```
tag:数学              # 精确匹配
tag:数学::代数        # 层级匹配
-tag:英语             # 排除
数学 OR 英语          # 或
数学 代数             # 与（空格分隔）
(数学 OR 英语) 代数   # 括号分组
```

#### 关键方法

```python
class TagSystem:
    def add_tag(record_id: str, tag: str) -> bool
    def remove_tag(record_id: str, tag: str) -> bool
    def get_tags(record_id: str) -> List[str]
    def search_with_operators(query: str) -> List[str]
    def get_tag_tree() -> Dict
    def get_all_tags() -> List[str]
```

---

### 4.4 search_engine.py - 搜索引擎模块

#### 职责
- 全文搜索
- 标签搜索
- 高级搜索语法解析

#### 搜索语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `关键词` | 全文搜索 | `方程` |
| `"精确短语"` | 短语搜索 | `"一元二次方程"` |
| `tag:标签` | 标签搜索 | `tag:数学` |
| `-tag:标签` | 排除标签 | `-tag:英语` |
| `AND` | 与运算 | `数学 AND 方程` |
| `OR` | 或运算 | `数学 OR 英语` |
| `-` | 排除 | `-英语` |

#### AST解析

搜索引擎使用抽象语法树(AST)解析搜索查询：

```
查询: "数学 OR (英语 AND 语法)"

         OR
        /  \
      数学  AND
           /   \
         英语  语法
```

#### 关键类

```python
class TokenType(Enum):
    TAG = auto()
    TEXT = auto()
    PHRASE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()

class SearchEngine:
    def search(query: str, page: int, page_size: int) -> Dict
    def get_all_tags() -> List[str]
    def refresh()  # 刷新缓存
```

---

## 5. 数据结构

### 5.1 题目JSON格式

**文件路径**: `data/{question_id}.json`

```json
{
  "id": "20260321124856",
  "created_at": "2026-03-21 12:48:56",
  "question": {
    "items": [
      {
        "type": "text",
        "content": "解方程 x + 2 = 5"
      },
      {
        "type": "image",
        "config_id": "cfg_20260321124838_a1b2c3d4"
      },
      {
        "type": "richtext",
        "content": "...",
        "fragments": [
          {"text": "普通文本"},
          {"text": "下划线文本", "underline": true}
        ]
      }
    ]
  },
  "answer": {
    "items": [
      {
        "type": "text",
        "content": "x = 3"
      }
    ]
  },
  "tags": ["数学", "代数::方程"],
  "sub_questions": [
    {
      "id": "sq_001",
      "title": "小问1",
      "question_text": {
        "items": [...]
      },
      "tags": ["小问标签"]
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 题目ID，格式：YYYYMMDDHHMMSS |
| created_at | string | 是 | 创建时间 |
| question | object | 是 | 题目内容 |
| question.items | array | 是 | 内容项列表 |
| answer | object | 是 | 答案内容 |
| answer.items | array | 是 | 答案项列表 |
| tags | array | 否 | 标签列表 |
| sub_questions | array | 否 | 小问列表 |

#### Item类型

##### 文本项
```json
{
  "type": "text",
  "content": "普通文本内容"
}
```

##### 富文本项
```json
{
  "type": "richtext",
  "content": "原始HTML",
  "fragments": [
    {"text": "普通文本"},
    {"text": "下划线文本", "underline": true}
  ]
}
```

##### 图片项（存储格式）
```json
{
  "type": "image",
  "config_id": "cfg_20260321124838_a1b2c3d4"
}
```

##### 图片项（展开格式，API返回）
```json
{
  "type": "image",
  "config_id": "cfg_20260321124838_a1b2c3d4",
  "src": "img/20260321124838_90d2e800.png",
  "display": "center",
  "width": 300,
  "height": "auto",
  "charBox": {
    "fontSize": "medium",
    "size": 0.033,
    "x": 0.51,
    "y": 0.035
  },
  "splitLines": [0.3, 0.6]
}
```

---

### 5.2 images.json 格式

**文件路径**: `images.json`

```json
{
  "images": {
    "img_20260321124838_90d2e800": {
      "id": "img_20260321124838_90d2e800",
      "filename": "20260321124838_90d2e800.png",
      "path": "img/20260321124838_90d2e800.png",
      "created_at": "2026-03-21 12:48:38",
      "width": 800,
      "height": 600,
      "file_size": 12345
    }
  },
  "configs": {
    "cfg_20260321124838_a1b2c3d4": {
      "id": "cfg_20260321124838_a1b2c3d4",
      "image_id": "img_20260321124838_90d2e800",
      "display": "center",
      "width": 300,
      "height": "auto",
      "charBox": {
        "fontSize": "medium",
        "size": 0.033,
        "x": 0.51,
        "y": 0.035
      },
      "splitLines": [0.3, 0.6],
      "used_by": ["20260321124856"]
    }
  }
}
```

#### 图片元数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 图片唯一ID |
| filename | string | 文件名 |
| path | string | 相对路径 |
| created_at | string | 创建时间 |
| width | number | 图片宽度（像素） |
| height | number | 图片高度（像素） |
| file_size | number | 文件大小（字节） |

#### 图片配置字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 配置唯一ID |
| image_id | string | 关联的图片ID |
| display | string | 显示方式：center/float-left/float-right |
| width | number | 显示宽度 |
| height | string/number | 显示高度，通常为"auto" |
| charBox | object | 字框标注配置 |
| splitLines | array | 分割线位置（比例） |
| used_by | array | 使用该配置的题目ID列表 |

---

### 5.3 tags_data.json 格式

```json
{
  "records": {
    "题目ID": ["标签1", "标签2"]
  },
  "tag_tree": {
    "标签名": {
      "children": {
        "子标签": {}
      }
    }
  }
}
```

---

### 5.4 数据关系图

```
┌─────────────────┐
│  题目JSON文件    │
│  (data/*.json)  │
└────────┬────────┘
         │ 引用
         ▼
┌─────────────────┐      ┌─────────────────┐
│   图片配置       │──────│   图片元数据     │
│  (configs)      │ 引用  │   (images)      │
└─────────────────┘      └─────────────────┘
         │
         │ 追踪
         ▼
┌─────────────────┐
│   题目ID列表     │
│   (used_by)     │
└─────────────────┘

┌─────────────────┐      ┌─────────────────┐
│   题目JSON文件   │──────│   标签记录       │
│                 │ 拥有  │  (records)      │
└─────────────────┘      └────────┬────────┘
                                  │ 构建
                                  ▼
                         ┌─────────────────┐
                         │   标签树         │
                         │  (tag_tree)     │
                         └─────────────────┘
```

---

## 6. API接口

### 6.1 题目相关API

#### POST /api/save
保存题目（新建或更新）。

**请求体**:
```json
{
  "id": "20260321124856",
  "question": {
    "items": [...]
  },
  "answer": {
    "items": [...]
  },
  "tags": ["数学"],
  "sub_questions": [...]
}
```

**响应**:
```json
{
  "success": true,
  "id": "20260321124856",
  "filename": "20260321124856.json"
}
```

#### GET /api/questions
获取题目列表。

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 50 | 每页数量 |
| search | string | "" | 搜索关键词 |

**响应**:
```json
{
  "questions": [...],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2,
  "search_query": ""
}
```

#### PUT /api/questions/{id}
更新指定题目。

**请求体**: 同 POST /api/save

**响应**:
```json
{
  "success": true,
  "id": "20260321124856",
  "question": {
    // 展开后的完整题目数据
  }
}
```

#### DELETE /api/questions/{id}
删除指定题目。

**响应**:
```json
{
  "success": true,
  "id": "20260321124856"
}
```

---

### 6.2 图片相关API

#### POST /api/upload-image
上传图片。

**请求体**:
```json
{
  "image": "data:image/png;base64,iVBORw0KGgo..."
}
```

**响应**:
```json
{
  "success": true,
  "image_id": "img_20260321124838_90d2e800",
  "filename": "20260321124838_90d2e800.png",
  "path": "img/20260321124838_90d2e800.png"
}
```

#### GET /api/images
获取所有图片列表。

**响应**:
```json
{
  "success": true,
  "images": [...],
  "configs": [...]
}
```

#### GET /api/images/{config_id}
获取指定图片配置详情。

**响应**:
```json
{
  "success": true,
  "image": {...},
  "config": {...}
}
```

#### POST /api/split-image
分割图片。

**请求体**:
```json
{
  "src": "img/xxx.png",
  "splitLines": [0.3, 0.6],
  "width": 300
}
```

**响应**:
```json
{
  "success": true,
  "parts": [
    {"src": "/split_cache/xxx/part_000.png", "width": 300},
    {"src": "/split_cache/xxx/part_001.png", "width": 300},
    {"src": "/split_cache/xxx/part_002.png", "width": 300}
  ]
}
```

---

### 6.3 标签相关API

#### GET /api/tags
获取标签树和所有标签。

**响应**:
```json
{
  "success": true,
  "tag_tree": {...},
  "all_tags": ["数学", "英语", ...]
}
```

#### POST /api/questions/batch-add-tag
批量添加标签。

**请求体**:
```json
{
  "record_ids": ["20260321124856", "20260321124857"],
  "tag": "重要"
}
```

---

### 6.4 截图相关API

#### POST /api/screenshot/upload
上传截图到临时目录。

#### GET /api/screenshot/check
检查是否有待处理的截图。

#### POST /api/screenshot/consume/{screenshot_id}
消费截图，移动到正式目录。

---

## 7. 前端开发

### 7.1 页面结构

#### index.html - 录入页面
```
页面结构:
├── 顶部工具栏
│   ├── 标签输入
│   └── 保存按钮
├── 内容编辑区
│   ├── 题目Tab
│   │   ├── 内容列表
│   │   └── 添加按钮
│   └── 答案Tab
│       ├── 内容列表
│       └── 添加按钮
├── 预览区
│   └── A4预览
└── 小问区
    └── 小问列表
```

#### browse.html - 浏览页面
```
页面结构:
├── 左侧栏
│   ├── 搜索框
│   ├── 标签树
│   └── 题目列表
├── 中间栏
│   └── 题目详情/编辑区
└── 右侧栏
    └── 预览区
```

#### print.html - 打印页面
```
页面结构:
├── 控制面板
│   ├── 字号设置
│   └── 打印选项
└── 预览区
    └── A4页面预览
```

### 7.2 组件设计模式

#### 内容项渲染
```javascript
function renderContentListForTarget(contentList, items, target) {
    contentList.innerHTML = '';
    items.forEach((item, index) => {
        if (item.type === 'text') {
            // 渲染文本项
        } else if (item.type === 'image') {
            // 渲染图片项
        } else if (item.type === 'richtext') {
            // 渲染富文本项
        }
    });
}
```

#### 数据绑定
使用直接操作DOM的方式，无虚拟DOM：

```javascript
// 获取当前items
function getCurrentItems(target) {
    return target === 'question' ? questionItems : answerItems;
}

// 设置items
function setCurrentItems(items, target) {
    if (target === 'question') {
        questionItems = items;
    } else {
        answerItems = items;
    }
}
```

### 7.3 事件处理

#### 图片粘贴
```javascript
document.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    for (let item of items) {
        if (item.type.startsWith('image/')) {
            const file = item.getAsFile();
            handleImagePaste(file, currentTab);
        }
    }
});
```

#### 字框标注
```javascript
function openCharBoxModal(questionId, itemIndex, itemType, imgSrc) {
    // 打开字框标注模态框
    // 支持绘制字框和添加分割线
}

function confirmCharBox() {
    // 保存字框和分割线数据
    // 调用API更新题目
}
```

### 7.4 图片处理流程

```
用户粘贴/上传图片
       │
       ▼
handleImagePaste()
       │
       ▼
POST /api/upload-image
       │
       ▼
返回 image_id, path
       │
       ▼
创建本地item对象:
{
    type: 'image',
    image_id: result.image_id,
    config_id: null,
    src: result.path,
    ...
}
       │
       ▼
用户保存题目
       │
       ▼
POST /api/save
       │
       ▼
后端创建config_id
       │
       ▼
存储到JSON文件
```

---

## 8. AI模块

### 8.1 模块结构

```
ai/
├── __init__.py          # 模块初始化
├── base.py              # 基础类和工具函数
├── preprocessor.py      # 题目预处理分析
├── loader.py            # 数据加载器
├── prompts.py           # 提示词模板
├── preprocessing_prompt_v2.py
├── thinking_processor.py
├── immersion_processor.py
├── neural_reaction.py
└── evaluator.py
```

### 8.2 核心类

#### AIClient
单例模式的AI客户端：

```python
from ai.base import AIClient, AIConfig

# 使用默认配置
client = AIClient()

# 自定义配置
config = AIConfig(
    api_key="your-api-key",
    model="doubao-seed-2-0-pro-260215",
    max_output_tokens=131072
)
client = AIClient(config)

# 调用API
response = client.call(
    system_prompt="你是一个助手",
    user_content=[{"type": "input_text", "text": "你好"}]
)
```

#### 工具函数

```python
from ai.base import (
    encode_image_to_base64,      # 图片转base64
    get_image_media_type,        # 获取图片MIME类型
    build_input_content,         # 构建输入内容
    parse_items_text,            # 从items提取文本
    extract_image_paths_from_items,  # 从items提取图片路径
)
```

### 8.3 题目预处理

```python
from ai.preprocessor import generate_analysis_by_id

# 分析题目
analysis = generate_analysis_by_id(
    data_dir="data",
    question_id="20260321124856"
)

# 返回结构
analysis.question_basic_info        # 题目基本信息
analysis.module_1_basic_model_analysis    # 基础模型分析
analysis.module_2_student_trial_error_analysis  # 学生易错点
analysis.module_3_multi_dimensional_solution_analysis  # 多维解法
analysis.module_4_neural_stimulus_trigger_points    # 神经刺激点
```

### 8.4 添加新AI处理器

1. 创建处理器文件 `ai/new_processor.py`
2. 定义提示词模板
3. 实现处理函数：

```python
from ai.base import AIClient, build_input_content
from ai.loader import load_question_by_id

def generate_new_analysis(question_id: str) -> dict:
    question = load_question_by_id("data", question_id)
    if not question:
        return None
    
    client = AIClient()
    user_content = build_input_content(
        text=f"分析题目：{question.question_text}",
        image_paths=question.image_paths
    )
    
    response = client.call(
        system_prompt="你的提示词",
        user_content=user_content
    )
    
    return parse_response(response)
```

---

## 9. 扩展开发指南

### 9.1 添加新API

**步骤**:

1. 在 `app.py` 中添加路由：

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    try:
        data = request.json
        # 处理逻辑
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

2. 如需操作图片，调用 `image_manager`：

```python
image_id = image_manager.add_image(...)
config_id = image_manager.create_config(...)
```

3. 如需操作标签，调用 `tag_system`：

```python
tag_system.add_tag(record_id, tag)
tag_system.remove_tag(record_id, tag)
```

4. 如需刷新搜索，调用：

```python
search_engine.refresh()
```

### 9.2 添加新页面

**步骤**:

1. 创建 `static/new-page.html`
2. 复制现有页面的基础结构
3. 添加页面特定的样式和脚本
4. 如需新路由，在 `app.py` 添加：

```python
@app.route('/new-page')
def new_page():
    return send_from_directory('static', 'new-page.html')
```

### 9.3 添加新数据字段

**步骤**:

1. 更新数据结构（本节说明）
2. 修改保存逻辑（`/api/save`）
3. 修改读取逻辑（`/api/questions`）
4. 更新前端显示逻辑
5. 编写数据迁移脚本

**示例：添加"难度"字段**:

```python
# 1. 保存时处理
question_data['difficulty'] = data.get('difficulty', 'medium')

# 2. 读取时展开（如需要）

# 3. 迁移脚本
def add_difficulty_field():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                if 'difficulty' not in data:
                    data['difficulty'] = 'medium'
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 9.4 数据迁移注意事项

1. **始终备份**：迁移前备份 `data/` 目录
2. **增量迁移**：检查字段是否存在再添加
3. **向后兼容**：读取时提供默认值
4. **测试验证**：迁移后验证数据完整性

```python
# 迁移脚本模板
def migrate_data():
    # 1. 备份
    backup_dir = f"data_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copytree('data', backup_dir)
    
    # 2. 迁移
    for filename in os.listdir('data'):
        if filename.endswith('.json'):
            filepath = os.path.join('data', filename)
            with open(filepath, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                modified = False
                
                # 迁移逻辑
                if 'new_field' not in data:
                    data['new_field'] = 'default_value'
                    modified = True
                
                if modified:
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
    
    # 3. 验证
    print("迁移完成，请验证数据")
```

---

## 10. 开发规范

### 10.1 代码风格

- Python: 遵循 PEP 8
- JavaScript: 使用 4 空格缩进
- 命名: 
  - Python: snake_case（函数/变量）、PascalCase（类）
  - JavaScript: camelCase（函数/变量）、PascalCase（类）

### 10.2 文件命名

- Python模块: `snake_case.py`
- 数据文件: `{YYYYMMDDHHMMSS}.json`
- 图片文件: `{YYYYMMDDHHMMSS}_{random8}.{ext}`

### 10.3 错误处理

```python
# API错误处理模板
@app.route('/api/xxx', methods=['POST'])
def xxx():
    try:
        # 处理逻辑
        return jsonify({'success': True, ...})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 10.4 日志记录

建议添加日志：

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"处理题目: {question_id}")
logger.error(f"处理失败: {e}")
```

---

## 附录

### A. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| ARK_API_KEY | 火山引擎API密钥 | - |

### B. 依赖安装

```bash
pip install flask flask-cors pillow volcengine-python-sdk
```

### C. 启动命令

```bash
python app.py
# 访问 http://localhost:5000
```

### D. 常见问题

**Q: 图片显示404？**
A: 检查图片路径是否正确，确保 `img/` 目录存在且图片文件存在。

**Q: 标签搜索不生效？**
A: 确保 `tags_data.json` 与题目JSON同步，可重新运行初始化。

**Q: AI分析失败？**
A: 检查 `ARK_API_KEY` 环境变量是否设置正确。

---

*文档版本: 1.0*
*最后更新: 2026-04-03*
