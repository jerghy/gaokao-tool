# Checklist

- [x] AIContext 类正确实现，持有 data_dir 和 AIConfig
- [x] AIContext.question(id) 返回正确的 Question 对象
- [x] AIContext.search(query) 返回 Question 列表
- [x] Question 对象包含 question_text、answer_text、image_paths 属性
- [x] Question.ai(prompt) 正确调用 AI 并返回结果字符串
- [x] Question.process(prompt, output_field) 调用 AI 并保存到 JSON
- [x] Question.save(field, result) 正确保存结果到 JSON
- [x] Question.subs(tags) 正确过滤并返回子问题列表
- [x] list[Question].batch_ai() 批量处理功能正常工作
- [x] 向后兼容：原有 API 不受影响
- [x] 导入测试通过：`from ai import AIContext, Question`
