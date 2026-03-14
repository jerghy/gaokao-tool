# Anki 风格浏览界面 - 实现计划

## [ ] Task 1: 后端 API 扩展
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 app.py 中集成 tag_system.py
  - 添加获取标签树的 API 端点
  - 添加获取错题列表的 API 端点（支持按标签筛选、组合筛选 AND/OR）
  - 添加更新错题的 API 端点
  - 添加搜索错题的 API 端点（支持题目内容和标签搜索，支持多级标签）
  - 添加删除错题的 API 端点
  - 添加批量操作 API（批量加标签等）
- **Acceptance Criteria Addressed**: [AC-8, AC-9, AC-10, AC-11, AC-12]
- **Test Requirements**:
  - `programmatic` TR-1.1: GET /api/tags 返回完整标签树结构
  - `programmatic` TR-1.2: GET /api/questions 支持 tag 参数筛选，支持多个标签和 AND/OR 逻辑
  - `programmatic` TR-1.3: GET /api/questions 支持 search 参数搜索（题目内容和标签）
  - `programmatic` TR-1.4: PUT /api/questions/:id 正确更新错题内容和标签
  - `programmatic` TR-1.5: DELETE /api/questions/:id 正确删除错题并更新 tag_system
  - `programmatic` TR-1.6: POST /api/questions/batch-add-tag 正确为多个错题批量添加标签
- **Notes**: 需要初始化 tag_system 时使用 DATA_DIR 下的数据

## [ ] Task 2: 创建浏览界面 HTML 骨架
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建 browse.html 文件
  - 实现三栏式布局（左、中、右）
  - 添加基本的 CSS 样式
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `human-judgement` TR-2.1: 页面显示三栏布局，各区域有明显分隔
  - `human-judgement` TR-2.2: 样式与现有系统风格一致
- **Notes**: 参考 index.html 的样式风格

## [ ] Task 3: 实现左侧标签树组件
- **Priority**: P0
- **Depends On**: [Task 1, Task 2]
- **Description**: 
  - 实现标签树的渲染逻辑
  - 支持标签的展开/折叠
  - 点击标签触发筛选
  - 支持多选标签（用于组合筛选）
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-9]
- **Test Requirements**:
  - `programmatic` TR-3.1: 标签树从 API 获取并正确渲染层级结构
  - `programmatic` TR-3.2: 点击标签后触发错题列表的筛选
  - `programmatic` TR-3.3: 支持多选标签并设置 AND/OR 逻辑
  - `human-judgement` TR-3.4: 标签可以展开和折叠
- **Notes**: 层级标签使用 :: 分隔

## [ ] Task 4: 实现中间错题列表组件
- **Priority**: P0
- **Depends On**: [Task 1, Task 2]
- **Description**: 
  - 实现错题列表的渲染
  - 添加搜索框和搜索功能（支持题目内容和标签搜索）
  - 支持单选错题
  - 支持多选错题
  - 实现右键菜单进行批量操作
- **Acceptance Criteria Addressed**: [AC-4, AC-11, AC-12]
- **Test Requirements**:
  - `programmatic` TR-4.1: 无筛选时显示所有错题
  - `programmatic` TR-4.2: 搜索功能正常工作，匹配题目内容和标签
  - `programmatic` TR-4.3: 点击错题可以选中并在右侧显示
  - `programmatic` TR-4.4: 支持多选错题
  - `human-judgement` TR-4.5: 右键菜单显示批量操作选项
- **Notes**: 列表项显示题目的预览内容

## [ ] Task 5: 实现右侧编辑区域
- **Priority**: P0
- **Depends On**: [Task 1, Task 2, Task 4]
- **Description**: 
  - 复用 index.html 中的编辑组件
  - 显示选中错题的内容
  - 实现题目、答案的编辑
  - 实现标签的编辑
  - 添加保存按钮和功能
  - 添加删除按钮和功能
- **Acceptance Criteria Addressed**: [AC-6, AC-7, AC-10]
- **Test Requirements**:
  - `programmatic` TR-5.1: 选中错题后正确加载其内容
  - `programmatic` TR-5.2: 编辑题目/答案后保存，数据正确更新
  - `programmatic` TR-5.3: 添加/删除标签后保存，tag_system 数据正确更新
  - `programmatic` TR-5.4: 点击删除按钮后错题被正确删除
  - `human-judgement` TR-5.5: 编辑界面与 index.html 保持一致的体验
- **Notes**: 尽量复用 index.html 中的 JavaScript 逻辑

## [ ] Task 6: 实现批量操作功能
- **Priority**: P1
- **Depends On**: [Task 1, Task 4]
- **Description**: 
  - 实现批量加标签功能
  - 实现批量删除标签功能
  - 实现批量删除错题功能
- **Acceptance Criteria Addressed**: [AC-11]
- **Test Requirements**:
  - `programmatic` TR-6.1: 多选错题后批量加标签，所有选中错题都添加该标签
  - `programmatic` TR-6.2: 多选错题后批量删除标签，所有选中错题都移除该标签
  - `programmatic` TR-6.3: 多选错题后批量删除，所有选中错题都被删除
- **Notes**: 使用 tag_system.py 的批量操作功能

## [ ] Task 7: 路由集成和导航
- **Priority**: P1
- **Depends On**: [Task 2]
- **Description**: 
  - 在 app.py 中添加浏览界面的路由
  - 在 index.html 中添加跳转到浏览界面的链接
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-7.1: 访问 /browse 可以打开浏览界面
  - `human-judgement` TR-7.2: index.html 中有明显的入口链接
- **Notes**: 保持现有的 / 路由指向 index.html

## [ ] Task 8: 集成测试和优化
- **Priority**: P1
- **Depends On**: [Task 3, Task 4, Task 5, Task 6]
- **Description**: 
  - 端到端测试完整流程
  - 优化响应性能
  - 修复发现的 bug
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12]
- **Test Requirements**:
  - `programmatic` TR-8.1: 完整流程测试通过（浏览-筛选-搜索-编辑-保存-删除-批量操作）
  - `human-judgement` TR-8.2: 界面响应流畅，无明显卡顿
- **Notes**: 使用真实数据进行测试
