# Tasks

- [x] Task 1: 创建化学题目判断和渲染函数
  - [x] SubTask 1.1: 创建 `isChemistryQuestion()` 函数判断题目是否为化学题
  - [x] SubTask 1.2: 创建 `renderChemistryProcessingResult()` 函数渲染化学题目内容
  - [x] SubTask 1.3: 创建 `renderAccumulation()` 函数渲染 Accumulation 内容

- [x] Task 2: 创建 Difficulty Teaching 渲染函数
  - [x] SubTask 2.1: 创建 `renderDifficultyTeaching()` 函数渲染难点教学内容
  - [x] SubTask 2.2: 实现根据 `selected_difficulty_ids` 和 `Difficulties` 获取 `DifficultyName` 的逻辑
  - [x] SubTask 2.3: 将 Markdown 内容渲染为 HTML

- [x] Task 3: 添加 CSS 样式
  - [x] SubTask 3.1: 添加化学训练内容的样式类（.chemistry-processing）
  - [x] SubTask 3.2: 添加 Accumulation 项的样式类（.accumulation-item）
  - [x] SubTask 3.3: 添加 Difficulty Teaching 的样式类（.difficulty-teaching）

- [x] Task 4: 修改主渲染逻辑
  - [x] SubTask 4.1: 修改 `renderPreview()` 函数，增加化学题目判断分支
  - [x] SubTask 4.2: 在题目渲染中集成化学训练内容

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 4] depends on [Task 1, Task 2, Task 3]
