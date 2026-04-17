# Checklist

## 后端配置模块
- [x] config.py 中包含所有路径常量（BASE_DIR, IMG_DIR, DATA_DIR, SCREENSHOT_DIR, SPLIT_CACHE_DIR）
- [x] config.py 中包含所有文件路径常量（TAGS_DATA_PATH, IMAGES_DATA_PATH, PENDING_SCREENSHOTS_FILE）
- [x] app.py 中不再有硬编码路径

## 数据访问层
- [x] QuestionRepository 封装了题目 JSON 文件的 list_all 操作
- [x] QuestionRepository 封装了题目 JSON 文件的 get_by_id 操作
- [x] QuestionRepository 封装了题目 JSON 文件的 save 操作
- [x] QuestionRepository 封装了题目 JSON 文件的 delete 操作
- [x] TagRepository 封装了 TagSystem 的接口

## 服务层
- [x] QuestionService 包含 process_image_items 逻辑
- [x] QuestionService 包含 expand_image_items 逻辑
- [x] QuestionService 包含题目保存/更新/删除逻辑
- [x] QuestionService 包含标签同步逻辑
- [x] ImageService 包含图片上传逻辑
- [x] ImageService 包含图片分割逻辑
- [x] ImageService 包含图片查询逻辑
- [x] ScreenshotService 包含截图上传/检查/消费逻辑
- [x] ScreenshotService 包含截图过期清理逻辑
- [x] 无模块级全局可变状态（pending_screenshots 等）

## 路由层
- [x] question_routes.py 包含所有题目相关 API 路由
- [x] image_routes.py 包含所有图片相关 API 路由
- [x] screenshot_routes.py 包含所有截图相关 API 路由
- [x] tag_routes.py 包含所有标签相关 API 路由
- [x] page_routes.py 包含所有页面路由
- [x] 路由函数中无业务逻辑（仅参数提取、调用 Service、格式化响应）

## 应用工厂
- [x] app.py 使用 create_app() 工厂模式
- [x] 所有 Blueprint 正确注册
- [x] 错误处理器正确注册
- [x] 应用可正常启动

## 前端 JS 模块提取
- [x] browse.html 内联 JS 已提取到 browse.js
- [x] index.html 内联 JS 已提取到 index.js
- [x] print.html 内联 JS 已提取到 print.js
- [x] 各 HTML 页面仅保留初始化调用

## 前端公共 CSS
- [x] common.css 包含跨页面重复的 CSS 规则
- [x] 各页面正确引用 common.css
- [x] 各页面无重复 CSS 规则

## API 兼容性
- [x] 所有 API 端点路径不变
- [x] 所有 API 请求/响应格式不变
- [x] 所有页面路由正常工作

## 功能验证
- [x] 题目录入功能正常（API 200）
- [x] 题目浏览功能正常（API 200）
- [x] 题目编辑功能正常（API 200）
- [x] 题目删除功能正常（API 200）
- [x] 图片上传功能正常（API 200）
- [x] 图片分割功能正常（API 200）
- [x] 字框标注功能正常（API 200）
- [x] 标签管理功能正常（API 200）
- [x] 搜索功能正常（API 200）
- [x] 截图功能正常（API 200）
- [x] 打印功能正常（页面 200）
- [x] 训练功能正常（API 200）
- [x] 无 Python 运行时错误
