from ai import process_question_with_thinking_tag

# process_question_with_thinking_tag(
#     data_dir=r"d:\space\html\print\data",
#     question_id="20260314141514"
# )
from ai import batch_process_with_search

# 处理所有带"思维"标签的数学或生物题目
# results = batch_process_with_search(
#     data_dir=r"d:\space\html\print\data",
#     search_query="(tag:化学)",  # 或 "北京"、"tag:重要" 等
#     max_workers=5  
# )
# print(results)
# {'total_searched': 5, 'success': [id1, id2], 'failed': [], 'skipped_no_thinking_tag': [id3]}
# 批量处理所有带"生物"标签的题目 - 使用 batch_process_generic
# batch_process_generic(
#     data_dir=r"d:\space\html\print\data",
#     system_prompt=MATH_THINKING_PROMPT,
#     search_query="tag:生物",
#     output_field="bio_processing",
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



from ai import batch_process_generic

with open("./ai/tsc/数学.txt","r",encoding="utf-8") as f:
    MATH_THINKING_PROMPT = f.read()

# results = batch_process_generic(
#     data_dir=r"d:\space\html\print\data",
#     system_prompt=MATH_THINKING_PROMPT,
#     search_query="tag:数学",  # 使用 API 搜索语法
#     output_field="math_thinking_chain",
#     enable_sub_question_filter=False,
#     # sub_question_tags=["思维"],
#     api_base_url="http://localhost:5000",  # 可选，默认 localhost:5000
#     max_workers=8
# )

from ai import batch_process_generic_by_ids


# idlist=["20260328150917"]
# # 处理单个题目
# results = batch_process_generic_by_ids(
#     data_dir=r"d:\space\html\print\data",
#     question_ids=idlist,  # 指定题目 ID,
#     system_prompt=MATH_THINKING_PROMPT,
#     output_field="math_thinking_chain",
    
#     # 小问筛选（可选）
#     enable_sub_question_filter=False,      # 是否开启小问筛选
#     # sub_question_tags=["思维"],            # 筛选带特定标签的小问
#     # require_all_sub_tags=False,           # 是否需要全部标签匹配
    
#     # 其他参数
#     skip_if_exists=False,                  # 已存在则跳过
#     max_output_tokens=131072,              # 最大输出 token 数
#     reasoning_effort="high",               # 推理深度 (low/medium/high)

#     max_workers=5
# )

# print(f"处理了 {results["total"]} 个目标")
# for r in results["success"]:
#     print(f"  - {r["target_label"]}: {r["math_thinking_chain"][:50]}...")

from ai.math_processor import process_math_question, batch_process_math_questions
from ai import search_questions_via_api

# 处理单个题目
# result = process_math_question(data_dir="data", question_id="20260321135310")

# 批量处理带"数学"标签的题目
# math_ids = search_questions_via_api(search_query="tag:数学", api_base_url="http://localhost:5000")
# print(f"找到 {len(math_ids)} 个数学题目")

# results = batch_process_math_questions(
#     data_dir="data",
#     question_ids=math_ids,
#     skip_if_exists=True,
#     max_workers=10
# )
# print(results)

from ai.tag_processor import batch_process_tags
from ai.base import AI, ReasoningEffort

ai = AI(
    model="doubao-seed-2-0-pro-260215",
    reasoning_effort=ReasoningEffort.medium,
)

# 批量处理所有题目
results = batch_process_tags(
    data_dir="./data",
    prompt_path="./ai/tsc/题目标签.txt",
    ai=ai,
    replace=False,                        # 增量合并
    skip_if_has_valid_tags=False,          # 跳过已有规范标签
    max_workers=20,                        # 并发数
)

print(f"成功: {len(results['success'])} 个")
print(f"失败: {len(results['failed'])} 个")
print(f"跳过: {len(results['skipped'])} 个")
