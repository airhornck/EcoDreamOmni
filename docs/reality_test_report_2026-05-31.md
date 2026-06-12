# EcoDreamOmni 真实性测试报告

> 执行时间: 2026-05-31T14:56:23.627031
> 执行环境: localhost (Docker Compose)
> Cookie: 使用用户提供的小红书真实Cookie
> LLM Key: sk-cef65d7e728d43d79a4a23d642faa6d0

## 汇总

| 指标 | 数值 |
|------|------|
| 总计 | 16 |
| 通过 | 16 |
| 失败 | 0 |
| 跳过 | 0 |

## 详细结果

| Phase | 用例 | 状态 | 详情 |
|-------|------|------|------|
| A | TC-A1 平台选择动态加载 | PASS | 返回 4 个平台: xiaohongshu, bilibili, douyin, wechat_official |
| A | TC-A2 内容格式二级联动 | PASS | 小红书格式: 图文, 视频, 仅文字 |
| A | TC-A3 账号池按平台过滤 | PASS | 账号池共 3 个账号，小红书 1 个 |
| A | TC-A4 智能模板推荐 | PASS | 推荐模板: 图文内容生产工作流 (is_fallback=False) |
| A | TC-A5 日配额硬限制 | PASS | 账号 小红的猫 quota=1 posts_today=0 |
| A | TC-A6 生命周期配额 | PASS | lifecycle=warmup daily_quota=1 |
| B | TC-B2 新模板加载验证 | PASS | 共 8 个模板，新增4个全部加载: ['content_creation_note_image', 'content_creation_video_clone', 'content_creation_video_original', 'content_creation_text_article'] |
| B | TC-B1 标准工作流节点流转 | PASS | 任务创建成功: c382fc9d-a93a-4196-899f-b7fb78fa243e, status=human_wait, node_index=6 |
| B | TC-B4 content_format 注入上下文 | PASS | task.content_format=None, status=human_wait |
| C | TC-C1 前置-工作流到达human_wait | PASS | current_node_index=6, execution_id=exec_A3a0Y8cOy2o |
| C | TC-C1 审核台可查看任务 | PASS | conclusion 存在, platform=xhs |
| C | TC-C1 APPROVE 驱动发布 | PASS | 新状态: completed, review_decision=APPROVE |
| C | TC-C2 REJECT 终止工作流 | PASS | 状态变为 failed |
| D | TC-D1 日配额检查 | PASS | posts_today=1/1 |
| D | TC-D4 Cookie 隔离与健康检查 | PASS | healthy=False, user_id=, nickname= |
| E | TC-E1 小红书真实发布 | PASS | 任务已 completed，execution_id=exec_A3a0Y8cOy2o |
