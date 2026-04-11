import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)

sys.path.insert(0, r'd:\space\html\print')

from ai.workflow import AIContext
from ai.math_processor import batch_process_math_questions

DATA_DIR = r'd:\space\html\print\data'

def get_math_question_ids(data_dir: str) -> list[str]:
    ctx = AIContext(data_dir=data_dir)
    questions = ctx.search_local("数学")
    return [q.id for q in questions]

if __name__ == '__main__':
    question_ids = get_math_question_ids(DATA_DIR)
    print(f"找到 {len(question_ids)} 个数学题目")
    
    result = batch_process_math_questions(
        data_dir=DATA_DIR,
        question_ids=question_ids,
        skip_if_exists=False,
        max_workers=10
    )
    print(f"\n处理完成: 总数={result['total']}, 成功={result['success']}, 失败={result['failed']}, 跳过={result['skipped']}")
