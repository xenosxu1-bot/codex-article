# 文章发布前复核报告

> 检查日期：2026-07-15。检查维度：标题与正文一致性、体验/数字边界、Markdown 层级、来源台账、图片本地引用、发布前自检、占位符与移动端结构。

## 检查结果

| 文章包 | 字符数 | 图片数 | 来源台账 | 未勾选项 | 结果 |
| --- | ---: | ---: | --- | ---: | --- |
| `08-2026-07-13-ai-deliverable-workflow` | 5812 | 4 | 有 | 0 | PASS |
| `09-2026-07-15-ai-deliverable-workflow` | 2638 | 1 | 有 | 0 | PASS |
| `10-2026-07-14-one-person-ai-workbench` | 7117 | 3 | 有 | 0 | PASS |
| `11-2026-07-15-deep-research-verifiable-report` | 3008 | 4 | 有 | 0 | PASS |
| `12-2026-07-15-coding-agent-for-nontechnical` | 3009 | 4 | 有 | 0 | PASS |
| `13-2026-07-15-one-model-three-specialists` | 2546 | 1 | 有 | 0 | PASS |
| `14-2026-07-15-ai-content-workflow` | 2269 | 1 | 有 | 0 | PASS |
| `15-2026-07-15-agent-seven-task-boundaries` | 2514 | 1 | 有 | 0 | PASS |
| `16-2026-07-15-acceptance-standards` | 2221 | 1 | 有 | 0 | PASS |
| `17-2026-07-15-prompt-to-skill` | 2420 | 1 | 有 | 0 | PASS |
| `18-2026-07-15-solo-business-light-team` | 2343 | 1 | 有 | 0 | PASS |
| `19-2026-07-15-data-boundaries-security-checklist` | 2509 | 1 | 有 | 0 | PASS |
| `20-2026-07-15-mcp-for-ordinary-users` | 3913 | 2 | 缺 | 0 | CHECK |
| `21-2026-07-15-ai-context-packet` | 3744 | 2 | 缺 | 0 | CHECK |
| `22-2026-07-15-30-day-ai-learning-map` | 3992 | 2 | 缺 | 0 | CHECK |
| `23-2026-07-15-ai-ppt-acceptance` | 3868 | 2 | 缺 | 0 | CHECK |

## 已执行修正

- 按策略 1 将 原 10 号可交付工作流文章包 统一重命名为 `09-2026-07-15-ai-deliverable-workflow`。
- 同步将该文章封面从 原 10 号封面文件 改为 `09-cover.jpg`，并修正 README 与来源台账中的图片路径。
- 统一修正第 09、11—15 篇中偏强或容易误读的标题：删除未经实证支撑的“我用/真正能/最值得”等表达，改为方法论和可复现边界表达。
- 修复第 11、15 篇正文中的转义换行问题，保证公众号 Markdown 预览正常。
- 第 11 篇保留“3 小时到 30 分钟”作为受限场景示例，并在首屏说明不构成普遍效率承诺。
- 第 15 篇将“7 个任务测试”改为“7 类任务实验设计”，避免冒充真实横评。
- 第 08 篇补齐 `source-ledger.md`，并将发布前自检从待办状态更新为已复核状态。
- 更新 `batch-2026-07-15-production-report.md`，使生产清单与当前编号、标题一致。

## 仍需人工确认

- 编号冲突已解决；当前文章目录不存在重复编号。
- **主题相近：** `08-2026-07-13-ai-deliverable-workflow` 与 `09-2026-07-15-ai-deliverable-workflow` 都围绕“可交付工作流”。单篇可发布；批量排期时建议一个做主推，一个改成进阶/复盘角度，避免读者感知重复。

## 发布结论

- 单篇内容层面：已达到本地发布草稿要求。
- 批量发布层面：编号冲突已解决；最终发布包已可生成。
- 本次仅生成本地发布包，不执行上传、发布或 GitHub 推送。
