from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

_SKIP_KEYWORDS = ("已存在", "跳过", "no_thinking_tag", "无现有思考过程", "已有规范标签", "无目标")


@dataclass
class BatchProgress:
    total: int
    success: list = field(default_factory=list)
    failed: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    desc: str = "处理"

    def summary(self) -> str:
        lines = [
            f"{'='*40}",
            f"  {self.desc} 批处理完成",
            f"  总计: {self.total}",
            f"  成功: {len(self.success)}",
            f"  失败: {len(self.failed)}",
            f"  跳过: {len(self.skipped)}",
        ]
        if self.failed:
            lines.append("  失败详情:")
            for item in self.failed:
                lines.append(f"    - {item['id']}: {item['reason']}")
        lines.append(f"{'='*40}")
        return "\n".join(lines)


def run_batch(
    process_fn: Callable,
    items: list,
    max_workers: int = 3,
    skip_fn: Callable | None = None,
    desc: str = "处理",
    item_id_fn: Callable | None = None,
) -> BatchProgress:
    _item_id_fn = item_id_fn or (lambda x: x if isinstance(x, str) else str(x))
    progress = BatchProgress(total=len(items), desc=desc)

    if not items:
        logger.info(progress.summary())
        return progress

    to_process = []
    for item in items:
        item_id = _item_id_fn(item)
        if skip_fn and skip_fn(item):
            progress.skipped.append(item_id)
            logger.info(f"[跳过] {item_id}")
        else:
            to_process.append(item)

    total_to_process = len(to_process)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(process_fn, item): item for item in to_process
        }
        for idx, future in enumerate(as_completed(future_to_item), 1):
            item = future_to_item[future]
            item_id = _item_id_fn(item)
            try:
                result = future.result()
            except Exception as exc:
                progress.failed.append({"id": item_id, "reason": str(exc)})
                logger.info(f"[{idx}/{total_to_process}] ✗ {item_id}: {exc}")
                continue

            rid = result.get("id", item_id)
            success = result.get("success", False)
            message = result.get("message", "")

            is_skip = any(kw in message for kw in _SKIP_KEYWORDS)

            if success and not is_skip:
                progress.success.append(rid)
                logger.info(f"[{idx}/{total_to_process}] ✓ {rid}: {message}")
            elif is_skip:
                progress.skipped.append(rid)
                logger.info(f"[{idx}/{total_to_process}] ⊘ {rid}: {message}")
            else:
                progress.failed.append({"id": rid, "reason": message})
                logger.info(f"[{idx}/{total_to_process}] ✗ {rid}: {message}")

    logger.info(progress.summary())
    return progress
