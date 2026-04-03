# Tasks

- [x] Task 1: 创建向量化和合并模块 `ai/question_vectorizer.py`
  - [x] SubTask 1.1: 实现文本向量化函数 `get_embedding(text)` 使用火山引擎API
  - [x] SubTask 1.2: 实现批量向量化函数 `vectorize_questions(json_file)` 读取JSON并批量向量化
  - [x] SubTask 1.3: 实现向量保存函数 `save_embeddings(json_file, questions)` 增量保存向量到JSON

- [x] Task 2: 实现相似度计算功能
  - [x] SubTask 2.1: 实现余弦相似度计算函数 `cosine_similarity(vec1, vec2)`
  - [x] SubTask 2.2: 实现相似题目查找函数 `find_similar_questions(json_file, threshold)` 找出所有相似度高于阈值的题目对

- [x] Task 3: 实现AI合并功能
  - [x] SubTask 3.1: 设计AI合并prompt，判断是否合并并生成合并结果
  - [x] SubTask 3.2: 实现AI合并函数 `merge_similar_questions(similar_pairs)` 调用AI处理相似题目对
  - [x] SubTask 3.3: 实现合并结果保存函数，将合并后的题目保存到JSON

- [x] Task 4: 整合主流程
  - [x] SubTask 4.1: 在 `judgment_questions.py` 中添加命令行入口
  - [x] SubTask 4.2: 支持命令行参数：`--vectorize`（向量化）、`--find-similar`（找相似）、`--merge`（AI合并）

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 1, Task 2, Task 3]
