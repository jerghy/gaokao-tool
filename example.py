from tag_system import TagSystem, MatchType

ts = TagSystem("example_tags.json")

print("=" * 60)
print("1. 基本用法")
print("=" * 60)

ts.add_tag("笔记001", "数学")
ts.add_tag("笔记001", "重要")
ts.add_tag("笔记002", "英语")
ts.add_tag("笔记002", "复习")

print(f"笔记001 的标签: {ts.get_tags('笔记001')}")
print(f"笔记002 的标签: {ts.get_tags('笔记002')}")
print(f"笔记003 的标签: {ts.get_tags('笔记003')}")

print("\n" + "=" * 60)
print("2. 多级标签")
print("=" * 60)

ts.add_tag("笔记003", "数学::代数::一元二次方程")
ts.add_tag("笔记003", "数学::几何::三角形")
ts.add_tag("笔记004", "数学::代数::二元一次方程组")
ts.add_tag("笔记005", "英语::语法::时态")
ts.add_tag("笔记006", "英语::词汇::托福词汇")

print(f"笔记003 的标签: {ts.get_tags('笔记003')}")
print(f"笔记004 的标签: {ts.get_tags('笔记004')}")

print("\n所有标签:")
for tag in ts.get_all_tags():
    print(f"  - {tag}")

print("\n标签树结构:")
import json
print(json.dumps(ts.get_tag_tree(), ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("3. 各种搜索方法")
print("=" * 60)

print(f"\n精确搜索 '数学': {ts.search('数学', MatchType.EXACT)}")
print(f"前缀搜索 '数学::': {ts.search('数学::', MatchType.PREFIX)}")
print(f"后缀搜索 '方程': {ts.search('方程', MatchType.SUFFIX)}")
print(f"包含搜索 '代数': {ts.search('代数', MatchType.CONTAINS)}")
print(f"正则搜索 '数学.*几何': {ts.search('数学.*几何', MatchType.REGEX)}")

print("\n" + "=" * 60)
print("4. 逻辑运算符搜索")
print("=" * 60)

print(f"\nAND 搜索 '数学 AND 重要': {ts.search_with_operators('数学 AND 重要')}")
print(f"OR 搜索 '数学 OR 英语': {ts.search_with_operators('数学 OR 英语')}")
print(f"NOT 搜索 '数学 NOT 几何': {ts.search_with_operators('数学 NOT 几何')}")
print(f"括号分组 '(数学 OR 英语) AND 重要': {ts.search_with_operators('(数学 OR 英语) AND 重要')}")
print(f"复杂查询 '数学:: AND (重要 OR 复习) NOT 已删除': {ts.search_with_operators('数学:: AND (重要 OR 复习) NOT 已删除')}")

print("\n" + "=" * 60)
print("5. 批量操作")
print("=" * 60)

print("\n批量添加标签 '重要' 到笔记005, 笔记006:")
result = ts.batch_add_tag(["笔记005", "笔记006"], "重要")
print(result)

print(f"\n笔记005 当前标签: {ts.get_tags('笔记005')}")
print(f"笔记006 当前标签: {ts.get_tags('笔记006')}")

print("\n批量移除标签 '重要' 从笔记005, 笔记006:")
result = ts.batch_remove_tag(["笔记005", "笔记006"], "重要")
print(result)

print(f"\n笔记005 移除后标签: {ts.get_tags('笔记005')}")
print(f"笔记006 移除后标签: {ts.get_tags('笔记006')}")

print("\n" + "=" * 60)
print("6. 标签树与层级")
print("=" * 60)

ts.add_tag("笔记007", "物理::力学::牛顿三定律")
ts.add_tag("笔记008", "物理::电磁学::欧姆定律")

print("物理相关笔记:")
print(ts.search_with_operators("物理::"))

print("\n删除标签 '英语::语法::时态' 从系统:")
ts.delete_tag_from_system("英语::语法::时态")

print("\n删除后的标签树:")
print(json.dumps(ts.get_tag_tree(), ensure_ascii=False, indent=2))

print("\n删除后的所有标签:")
for tag in ts.get_all_tags():
    print(f"  - {tag}")
