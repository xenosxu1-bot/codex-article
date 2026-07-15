---
name: article-wechat
description: 创建、修订、审核、发布和入库维护中文微信公众号及 AI 自媒体文章。用于选题、内容 Brief、资料研究、正文写作、标题、封面与配图、Markdown 排版、事实核查、版权检查、AI 质检、复盘；当用户要求文章入库、分类、索引、发布记录、知识库维护，或明确要求发布、上传、推送、同步到 GitHub 时，按知识库维护与编号发布流程执行。
---

# article-wechat

用于交付可发布的中文公众号文章和内容生产包，而不是只给一段泛文案。默认遵循：事实可核验、图片可追溯、格式适合移动端、发布动作可回滚、入库结构可持续维护。

## 启动顺序

1. 先读取 `references/recurring-rules.md`。
2. 判断任务模式，并在交付中说明关键假设。
3. 按需读取参考文件：
   - 输出契约：`references/output-contract.md`
   - 完整流程：`references/ai-media-production-system.md`
   - 文章生成方案：`references/article-generation-playbook.md`（用户要求统一后续文章生成方案、按方案写文章、生成新文章或沉淀文章流程时必读）
   - 选题与系列规划：`references/topic-selection-and-series-planning.md`（用户要求热门选题、选题库、内容规划、栏目或连续发文时必读）
   - 写作标准：`references/editorial-standards.md`
   - 事实核查：`references/fact-check-policy.md`
   - 视觉与版权：`references/visual-policy.md`
   - 质检清单：`references/qa-checklist.md`
   - GitHub 发布：`references/publishing-github.md`
   - 文章知识库维护：`references/article-knowledge-base-workflow.md`（用户要求文章入库、分类、索引、发布记录、知识库维护、持续更新或整理仓库时必读）
   - 正文模板：`references/wechat-article-template.md`
4. 交付前完成内容真实性与基本格式核验；正文不附发布前检查或参考资料区块。

## 规则优先级

如文档之间出现冲突，按以下顺序执行：用户本次明确指令 > `SKILL.md` > `references/recurring-rules.md` > 对应专项文档（如 `article-knowledge-base-workflow.md`、`publishing-github.md`、`output-contract.md`）> 旧版参考文档。发布触发条件以本文件和 `references/publishing-github.md` 为准。

## 任务模式

| 模式 | 触发 | 默认输出 | 是否发布 |
| --- | --- | --- | --- |
| 仅选题 | 用户要选题、方向、栏目 | 5-10 个选题卡和评分 | 否 |
| 仅草稿 | 用户要写一篇草稿、初稿、改写 | Markdown 正文，可附标题候选 | 否 |
| 完整生产包 | 用户要完整文章、可发布包、图文包 | 正文、图片、标题评分与真实性核验结果 | 否 |
| 审核修订 | 用户提供已有文章要求检查、优化 | 问题清单、修订建议、必要时给修订稿 | 否 |
| 知识库维护 | 用户要求文章入库、分类、索引、发布记录、整理仓库、持续更新 | 中文分类目录、总索引、分类/系列/标签索引、发布记录、维护清单 | 按用户要求；若涉及推送则是 |
| 发布到 GitHub | 用户明确说发布、上传、推送、同步到 GitHub | 编号、入库、索引更新、提交、推送、发布记录 | 是 |

**发布采用模式 C：只有用户明确要求“发布/上传/推送/同步到 GitHub”时，才执行编号、入库、更新索引、提交和推送。** 单纯“写文章、做草稿、做完整生产包”不触发发布。

## 信息缺失处理

可以合理假设：目标渠道为微信公众号、语气为有判断有边界的中文创作者口吻、默认交付为本地 Markdown 草稿或生产包。

必须询问或标记待确认：是否发布到 GitHub、是否使用真实图片或 AI 视觉、是否涉及医疗/法律/金融等高风险建议、是否使用未公开资料、是否使用第一人称真实经历或测试结果。

## 不可违反的底线

- 不虚构事实、数据、客户案例、采访、亲身测试或第一人称经历。
- 涉及最新工具、模型、价格、法规、人物、新闻或平台规则时，必须核验一手来源，并写清截至日期。
- 事实、推断、观点和假设必须分开表达。
- AI 视觉必须标注，不伪装成实拍、官方图、产品截图或真实案例。
- 图片必须本地可引用，并保留替代文本、图注、来源和授权说明。
- 标题不得捏造数字、制造恐慌、过度承诺，必须与正文一致。
- 交付前必须完成内容真实性核验；正文不附检查清单、参考资料或来源列表。
- 不把账号登录信息、密钥、Cookie、未公开资料或读者隐私写入 Skill、提示词或仓库。

## 正文格式硬规则

- 正文不使用中文全角引号；需要突出时使用 Markdown 加粗，例如 `**重点内容**`。
- 正文不使用 Markdown 分割线。
- 标题默认不使用问号，除非用户明确要求保留。
- 正文不设置发布前检查、参考资料、参考文献、资料来源或延伸阅读等区块。事实核验在内部完成，正文只保留经核验的结论与必要边界。

## 选题与系列规划

当用户要求热门选题、选题库、内容规划、栏目或连续发文时，先读取 `references/topic-selection-and-series-planning.md`。默认先完成既有内容去重、趋势与证据边界判断、选题评分、系列归类和建议发布顺序；未经用户明确要求，不因完成选题而自动写文或发布。

## 文章知识库维护

当用户要求“文章入库 + 分类 + 索引 + 发布记录”、知识库整理、仓库文章编排、持续更新或类似任务时，先读取 `references/article-knowledge-base-workflow.md`，并按项目实际 `AGENTS.md` / `README.md` 中的目录约定执行。默认目标是：保持中文文件夹和中文文件名、文章编号连续、素材集中管理、索引可查、发布记录可追溯、GitHub 推送可回滚。

知识库维护任务默认包括：确认目标仓库与分支、拉取远端最新状态、识别下一篇文章编号、选择主分类、补充 frontmatter 元数据、移动或新增文章和图片、更新总索引/分类索引/系列索引/标签索引、更新发布记录和维护清单、检查本地链接和图片路径。只有用户明确要求发布、推送或同步到 GitHub 时，才执行提交和推送。

## 默认产物

最小草稿见 `references/wechat-article-template.md`。完整生产包默认结构见 `references/output-contract.md`。发布到 GitHub 的编号和仓库规则见 `references/publishing-github.md`。文章入库、中文分类、索引、发布记录和持续更新规则见 `references/article-knowledge-base-workflow.md`。

## 长期规则记忆

维护 `references/recurring-rules.md` 作为长期编辑规范。只有用户明确提出长期要求，或同类规则重复出现且影响质量、安全、版权、事实核查或发布稳定性时，才写入长期规则。新规则与旧规则冲突时，将旧规则标记为 `replaced`，不要静默删除。

文章 frontmatter 仅用于元数据，不在正文展示；正文不重复文章标题作为 H1，可从摘要、封面或 `##` 小节开始。


## 后续文章生成默认流程

1. 先按 `references/article-generation-playbook.md` 建立 Brief：主题、目标读者、文章类型、目标动作、资料要求、图片要求、发布要求。
2. 再写正文：不同类型文章使用对应骨架；正文不重复展示一级标题。
3. 正式文章必须使用 HTML 注释包裹隐藏元信息块，避免 GitHub/Markdown 预览展示元信息表格。
4. 如需入库，继续执行 `references/article-knowledge-base-workflow.md`：编号、分类、图片、索引、发布记录、维护清单。
5. 如需提交或推送，继续执行 `references/publishing-github.md`，先校验再提交，不强推。
