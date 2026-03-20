# Tasks

- [x] Task 1: 创建 ai/ 目录结构
  - [x] SubTask 1.1: 创建 d:\space\html\print\ai\ 目录
  - [x] SubTask 1.2: 创建 ai/__init__.py 空文件

- [x] Task 2: 创建 ai/prompts.py - 提示词模块
  - [x] SubTask 2.1: 抽取 question_preprocessor.py 的 SYSTEM_PROMPT 为 get_neural_reaction_prompt()
  - [x] SubTask 2.2: 抽取 question_preprocessor_v2.py 的 SYSTEM_PROMPT_V2 为 get_preprocessing_prompt_v2()
  - [x] SubTask 2.3: 抽取 question_evaluator.py 的 SYSTEM_PROMPT 为 get_evaluation_prompt()

- [x] Task 3: 创建 ai/loader.py - 题目加载模块
  - [x] SubTask 3.1: 从 question_loader.py 迁移 ProcessedQuestion dataclass
  - [x] SubTask 3.2: 从 question_loader.py 迁移 parse_items, load_question_from_file, load_question_by_id 函数
  - [x] SubTask 3.3: 在 __init__.py 中导出 loader 模块

- [x] Task 4: 创建 ai/preprocessor.py - 预处理模块
  - [x] SubTask 4.1: 迁移 QuestionAnalysis dataclass
  - [x] SubTask 4.2: 迁移图片处理函数（encode_image_to_base64, get_image_media_type）
  - [x] SubTask 4.3: 迁移 generate_question_analysis 函数，调用 prompts.get_preprocessing_prompt_v2()
  - [x] SubTask 4.4: 迁移 generate_analysis_by_id, save_analysis_to_json, preprocess_and_save 函数
  - [x] SubTask 4.5: 在 __init__.py 中导出 preprocessor 模块

- [x] Task 5: 创建 ai/evaluator.py - 评估模块
  - [x] SubTask 5.1: 迁移 QualityEvaluation dataclass
  - [x] SubTask 5.2: 迁移图片处理函数
  - [x] SubTask 5.3: 迁移 evaluate_question_quality 函数，调用 prompts.get_evaluation_prompt()
  - [x] SubTask 5.4: 迁移其他评估相关函数
  - [x] SubTask 5.5: 在 __init__.py 中导出 evaluator 模块

- [x] Task 6: 创建 ai/batch_processor.py - 批量处理模块
  - [x] SubTask 6.1: 迁移 get_questions_without_reaction 函数
  - [x] SubTask 6.2: 迁移 process_single_question, batch_process 函数
  - [x] SubTask 6.3: 在 __init__.py 中导出 batch_processor 模块

- [x] Task 7: 更新 ai/__init__.py 公共导出
  - [x] SubTask 7.1: 导出所有公共接口供外部使用

- [x] Task 8: 删除原有Python文件
  - [x] SubTask 8.1: 删除 question_preprocessor.py
  - [x] SubTask 8.2: 删除 question_preprocessor_v2.py
  - [x] SubTask 8.3: 删除 question_loader.py
  - [x] SubTask 8.4: 删除 question_evaluator.py
  - [x] SubTask 8.5: 删除 batch_preprocess.py

# Task Dependencies
- Task 2, 3, 4, 5, 6 可并行执行（无依赖）
- Task 7 依赖 Task 2-6 完成
- Task 8 依赖 Task 1-7 完成
