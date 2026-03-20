from ai import process_question_with_thinking_tag

# process_question_with_thinking_tag(
#     data_dir=r"d:\space\html\print\data",
#     question_id="20260314141514"
# )
from ai import batch_process_with_search

# 处理所有带"思维"标签的数学或生物题目
results = batch_process_with_search(
    data_dir=r"d:\space\html\print\data",
    search_query="(tag:化学)",  # 或 "北京"、"tag:重要" 等
    max_workers=5  
)
print(results)
# {'total_searched': 5, 'success': [id1, id2], 'failed': [], 'skipped_no_thinking_tag': [id3]}
from ai import batch_process

# 批量处理所有带"生物"标签的题目
# batch_process(
#     data_dir=r"d:\space\html\print\data",
#     tags=["生物"],
#     require_all_tags=False,
#     max_workers=5
# )
# 处理"解题思考 AI" - 已有 thinking_processes 的题目

# 结果会跳过：没有"思维"标签的、没有 existing thinking_processes 的

# 处理"沉浸式思考 AI" - 已有 immersion_thinking 的题目
# from ai import batch_process_immersion_with_search

# # 搜索带"数学"标签且有thinking_processes的题目，生成沉浸式思考
# result = batch_process_immersion_with_search(
#     data_dir=r"d:\space\html\print\data",
#     search_query="tag:数学"
# )