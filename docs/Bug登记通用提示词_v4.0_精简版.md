# Bug登记提示词（一行粘贴版）

粘贴到Bug描述后：

> 请按以下流程处理此Bug：①按模板`docs/Bug记录/BUG-{日期}-{编号}_{标题}.md`生成Bug记录；②修复前强制检查6条架构红线（Agent禁直接DB/EventBus优先/MCP预留/六层Prompt完整/租户隔离/LLM路由经Hub），触及任一红线立即停止并报我决策；③检查质量门禁（TS/Lint 0 errors + Docker Build通过）与核心稳定性（最小修改/可回滚/数据兼容/API兼容）；④PRD对齐：新增功能需PRD定义+专家评审≥3.0分，Mode C画布禁加业务按钮；⑤修复后生成`docs/变更记录_v4.0/{日期}/CHG-xxx.md`并同步`文档总纲_v4.0.md`索引。
