# AGENTS.md

## 内容边界与创作自由

本项目只把以下内容视为硬边界：

- **事实边界**：涉及产品能力、版本、数据、案例、安装方式、政策或安全结论时，必须基于可核验资料；不把推测、模型生成内容或未验证经历写成事实。无法确认的内容要明确标注不确定性或待核验状态。
- **版权与品牌边界**：不得把未获授权的外部文章、图片、界面、字体、音视频或代码当作自有内容交付；外部素材保留来源、许可或使用范围记录。不得伪造官方 Logo、官方界面、客户案例、认证或授权关系。
- **安全与隐私边界**：不得提交密钥、Token、Cookie、个人敏感信息、内部地址、未脱敏日志或其他不应公开的数据；涉及安全操作时说明风险、权限和回滚条件，不把高风险操作包装成无风险步骤。

除上述边界外，文章和视觉内容不再设置项目级硬模板。标题、开头、篇章结构、篇幅、语气、标点、引用方式、代码块、表格、卡片、CTA、图片数量、图片位置、画布尺寸、配色、构图、图标、Logo、UI 元素、封面路线和生成阶段均可根据任务自行决定。`article-Skill` 可按需使用，但其风格、结构和视觉模板不再自动升级为本项目的强制规则。

- 正式文章仍需保持文件、链接和素材引用可追溯；这属于仓库完整性，不等于限制文章表达方式。
- 图片和排版检查只用于发现文件损坏、引用失效、疑似侵权或明显安全风险；审美、比例、留白、信息密度和风格差异默认交给人工判断，不因不符合历史模板而阻断。
- 文章可保留来源说明、参考资料、发布说明、Markdown 标题、代码块、宽表格或其他平台适配内容，只要不越过事实、版权和安全边界。

## 统一生产流程与校验原则

- 草稿、方案稿和内部试写可以直接写作，也可以先做 Brief、资料核验、配图或元数据登记；流程按任务复杂度选择，不强制固定顺序。
- 只有准备正式入库、平台发布或完成 Git 推送的文章，才必须执行选题、去重、必要的资料核验、资产登记、索引同步、统一检查和发布记录；临时 Demo、内部草稿和未入库素材不强制进入完整登记流程。
- `09-工具脚本` 中的检查脚本只应阻断可证实的事实、版权、安全、文件损坏、链接失效和仓库数据完整性问题；风格、结构和视觉偏好只能输出提醒，不能作为发布阻断条件。
- 是否生成封面、正文图、UI 示意图或其他视觉资产由任务决定；禁止伪造官方素材，但允许原创视觉、自定义图标和不同排版路线。
## 外部原文归档与内容去重

- 外部文章用于后续查重时，归档到 `10-外部原文归档/EXT-日期-序号-标题/`，不得占用正式文章编号、文章资产登记表或主 README 的正式文章表。账号后台原创文章同步时，先导出不含后台 token 的公开 URL 清单，再运行 `node 09-工具脚本/批量归档微信公众号原创.mjs --manifest <清单.json> --captured-at YYYY-MM-DD --report <同步记录.json>`。
- `source.html` 是不可人工编辑的原始快照；`content.md` 和 `content.txt` 只能由原始 HTML 自动转换，禁止把外部原文改写后当作正式文章。权利人已授权的账号原创原文，必须以 `--rights account-owner-authorized` 标注。
- 外部原文快照是追溯与去重基线；即使与已有正式文章重复度达到或超过 50%，也必须保留并在 `07-资料与流程/内容去重报告/` 登记关联，不能因相似度跳过或删除原文。该登记不构成新正式文章的查重豁免。
- 准备新增或重写正式文章并进入文章库前，先运行 `node 09-工具脚本/重建内容库索引.mjs`，再运行 `node 09-工具脚本/检查内容重复度.mjs --candidate <候选文件>`；草稿、临时 Demo 和未入库中间稿不强制执行。
- 重复度公式为“正文五字片段 Dice 相似度 × 85% + 标题二字片段 Dice 相似度 × 15%”；正式入库候选默认必须**低于 50%**。规范化标题或正文完全一致时直接阻止；重大重构如需人工放行，必须在选题或发布记录中说明新增价值和放行理由。重复度结果用于发现风险，不替代版权判断、事实核验和编辑判断。
- 检查结果为“人工复核”时，必须在选题或发布记录中说明新增角度；结果为“阻止”时，不得入库为新文章。

## 开源项目文章生产流程

- 涉及开源项目的事实、安装、安全、许可证、官方能力和版本信息，优先核对 GitHub README、官方文档及核心安全页面，并保留核验时间和来源。
- 使用案例必须标注为可复现模板、公开资料结论或已验证经历，不虚构客户案例、效率数据、生产经验、官方背书或授权关系。
- 官方界面、Logo、代码、截图和第三方素材必须按其许可或授权范围使用；自定义示意图要明确不是官方界面。
- 教程结构、章节数量、代码呈现方式、图片数量和视觉风格由文章目标与读者场景决定，不设项目级固定模板。
## 提交前检查

- 标准稿和深度稿在发布、推送或完成知识库维护前，先运行 `python 09-工具脚本/文章统一检查.py --id <文章编号> --strict`；再运行 `python 09-工具脚本/一键发布检查.py`。后者会串联索引重建、文章质量扫描、选题绑定、图片资产、本地链接、数量一致性、Git 格式、删除项和敏感信息检查。
- 检查 Markdown 链接、图片引用和代码块是否完整。
- 检查是否存在乱码、明显错别字和过时文件名。
- README 有新增文章或素材时，需要同步更新目录和图片说明。

## 选题阶段追踪

- 准备正式入库或发布的新增、重写文章，先登记或更新 `07-资料与流程/选题库.md`，并对照 `07-资料与流程/已发布文章去重登记.md` 做查重；草稿和内部试写可暂不登记，但不得只换标题重复旧文。
- 每启动一篇准备正式入库的后续文章，先把对应选题从 `S0 灵感池` 更新到 `S1 已立题`；后续按 `S2 已做资料/Brief`、`S3 初稿中`、`S4 待质检`、`S5 待发布`、`S6 已入库`、`S7 已复盘` 逐步记录。草稿和内部试写不要求跳过创作阶段去补齐这些状态。
- 如果选题暂缓、合并或放弃，分别标记为 `HOLD` 或 `DROP`，并写清原因、恢复条件或合并去向。
- 如果选题与已发布文章高度重叠，必须在选题库写清新增角度：新读者、新场景、新案例、新模板、新资料或团队版；否则不进入正文写作。
- 正式入库前应形成 Brief，至少包含目标读者、核心问题、不写什么、核心观点、交付物、资料要求、风险点和关联旧文；草稿可以先写后补。
- 正式入库或完成 Git 推送后，同步更新 `选题库.md`、`已发布文章去重登记.md`、状态跟踪文件、总索引、分类索引、系列索引、标签索引和发布记录，确保主题、阶段、编号、路径和 GitHub 状态可追溯。

## 选题库与同步管控

- `main` 作为个人生产与规划工作区，`prod` 作为确认后的共享知识库展示区；后续项目修改默认先落 `main`，用户确认后再同步 `prod`。
- 默认所有项目修改先在 `main` 完成；本地校验通过后仍不自动推送，只有用户明确确认提交或推送时才执行。不得直接把未确认改动提交到 `prod`。
- 同一 GitHub 仓库的不同分支不是隐私边界；真正私密内容不得放入公开仓库或公开分支历史。
- 每次新增选题、发布文章或同步分支后，都要能从选题库、资产登记表、发布记录和 Git 状态追溯来源与去向。

## 文章编号与上传

- 正式入库或发布的新增、重写文章，按 `07-资料与流程/后续文章生成方案.md` 完成必要的 Brief、正文、配图（如有）、索引和发布记录；不要求固定先后顺序。如果用户只要草稿，明确不入库、不登记为正式文章，也不提交发布记录。
- 正式文章使用两位数编号，新稿使用当前最高正式编号加 1。下架、删除或转为草稿不自动重排；仅当负责人明确批准“一次性编号迁移”时，才按 `07-资料与流程/编号变更记录.md` 中的映射执行。
- 正式入库的新文章默认采用“单篇文章包”：`分类/NN-中文标题/NN-中文标题.md` 为正文，文章专属素材放在同级 `assets/cover/` 与 `assets/figures/`，并使用“文章编号-中文文章标题-用途”命名；封面如有仅登记在 `article.json`、文章元数据和资产表中，不在正文嵌入或链接。资料来源、核验台账和发布记录仍集中维护在 `07-资料与流程/`，不复制进文章包。历史集中素材库继续保留并兼容，不强制回迁。临时预览、草稿图和实验素材放入 `.tmp/`，不进入正式资产登记。重命名时必须同步更新全部本地引用、README 与知识库索引。
- 新增文章时同步更新 `README.md`、`00-知识库导航/知识库总索引.md`、`分类索引.md`、`系列索引.md`、`标签索引.md`、`07-资料与流程/文章资产登记表.md` 和 `07-资料与流程/发布记录.md`；默认使用文件名前缀编号。删除、下架或转为草稿不修改既有文章文件名、图片和元数据；只有已批准的一次性迁移，才按《编号变更记录》同步这些内容。
- 更新 README、首页或知识库索引后，必须运行 `09-工具脚本/重建知识库索引.py` 或按其输出规则重建，确认展示编号与文章文件名前缀一致、链接可访问、资产登记表、元数据和正在使用的素材文件均已同步，需要时可依《编号变更记录》追溯。
- 更新 README、首页或知识库索引后，正式入库任务必须运行 `09-工具脚本/重建知识库索引.py`，确认展示编号与文件名前缀一致、链接可访问、资产登记表、元数据和正在使用的素材文件已同步；批量重排时另行检查文件、图片、元数据和映射记录，并按《编号变更记录》追溯。
- 分类文章下架、迁移或资产登记表删除某分类最后一篇文章时，也必须重建对应分类 `README.md`；空分类 README 应显示“暂无正式入库文章”，不得保留旧文章表格、旧链接或缺失图片引用。

### 知识库维护与查阅

- 读者首次进入知识库时，优先从 `00-知识库导航/阅读路径.md` 按目标开始；分类、系列、标签和总索引只负责查全，不重复维护阅读顺序说明。
- 正式文章的编号、标题、分类、系列、标签、路径、字数和入库状态，以 `07-资料与流程/文章资产登记表.md` 为当前汇总索引；标准稿和深度稿另以 `07-资料与流程/文章元数据/NN-中文标题.json` 记录单篇素材、来源、封面与检查结果。选题状态、发布记录、图片记录和下架记录分别按 `07-资料与流程/更新工作流.md` 的分工维护。
- 下架或合并文章时，必须更新 `07-资料与流程/下架文章与替代关系.md`；历史发布编号保留在记录中，需要批量重排时以 `编号变更记录.md` 为准。
- 新增、替换或清理图片后，运行 `09-工具脚本/图片资产检查.py`；文章包内的正文插图必须被该正文引用，文章包内封面必须与该文章编号匹配且不得作为正文链接；历史集中素材库按既有规则检查。未归属或已下架编号残留的图片不得直接忽略。
- 仓库文本文件使用 UTF-8 与 LF 换行；编辑器行为以根目录 `.editorconfig` 和 `.gitattributes` 为准。

- 默认完成本地修改和验证，不自动推送远端。只有用户明确要求提交、推送或同步时，才提交并推送 `main`；执行前先获取远端更新，确认没有未处理的冲突，禁止强推。


## main 到 prod 晋级发布规则

- 默认所有项目修改先在 `main` 完成；本地校验通过后仍不自动推送，只有用户明确确认提交或推送时才执行。不得直接把未确认改动提交到 `prod`。
- `prod` 只作为确认后的稳定发布分支；只有用户明确确认“同步到 prod”“发布到 prod”或同等表达后，才把 `main` 中已确认的提交合并或同步到 `prod`。
- 同步 `prod` 前先确认 `main` 与 `prod` 的差异，优先保留 `prod` 已有的知识库导航、发布记录等稳定规则，再合入 `main` 的最新内容。
- 同步 `prod` 后必须至少完成文章质量扫描、Markdown 链接/图片检查和 Git 格式检查；检查通过后再推送 `prod`。
- 同步完成后向用户说明：`main` 提交、`prod` 提交、检查结果、是否已推送，以及当前工作区是否仍有未提交文件。

## 知识库目录约定

- 顶层只保留 GitHub/Codex 必需入口文件（`README.md`、`AGENTS.md`）和中文一级目录。
- 文章按主分类进入中文目录；交叉分类通过索引和标签解决，不复制正文文件。
- 素材、脚本、流程文档分别放入 `08-素材库/`、`09-工具脚本/`、`07-资料与流程/`；过时脚本和旧提示词模板放入 `07-资料与流程/历史脚本与模板/`，未使用图片放入 `08-素材库/图片/归档/` 并登记；不保留整包发布归档。

## 文章质量与平台适配

- 发布版可以采用适合目标平台的任意文章结构，不强制 H1、引用式开头、固定结尾、固定加粗数量、固定表格列数、代码块转换或图片模块。
- 平台兼容检查只关注事实、版权、安全、隐私、链接和文件完整性；排版、语气、阅读节奏和视觉选择由作者或项目负责人决定。
- 公开正文可以保留来源、参考资料、审核说明或其他必要边界说明；不要把密钥、个人信息、未授权原文或未核验结论放入正文。
- 文章质量扫描中的风格类提醒不作为 P0/P1 阻断条件，确有风险时以人工复核为准。
## 后续任务自动提交约定

- 默认完成本地修改和验证，不自动提交或推送。只有用户明确要求提交、推送或同步时，才执行对应的 Git 操作；用户明确要求“仅本地修改”或“仅草稿”时，不提交、不推送。
- 自动提交前必须先获取远端 `main` 最新状态，确认没有未处理的远端更新或冲突；禁止强推。
- 提交说明要简洁写清本次文章、索引、素材或流程变更范围；提交后向用户说明提交哈希、推送分支和本地是否仍有未提交文件。


## Workspace Boundary and Artifact Retention

- `D:\projects_git\Codex_article` is the only Git root and the long-term source of truth. Run Git commands there. Do not recreate `.publication/codex-article`, a nested Git repository, a release copy, or an unpacked repository backup inside this project.
- Keep publishable articles, indexes, source ledgers, and registered assets in the canonical repository. The previous outer `articles/` staging directory was removed after the repository promotion; do not recreate it as a parallel source of truth.
- Treat `.tmp/` as task-local, ignored working space. Remove generated previews, temporary scripts, fetched image batches, and diagnostic files after the related visual or publishing check has completed; retain only artifacts needed by an active task or an unresolved review.
- Do not keep the same deliverable as an unpacked release folder, a local ZIP, and a copied checkout. Use the canonical Git history and versioned GitHub Releases for reproducible releases; keep only one documented recovery copy when a recovery copy is truly required.
- `10-外部原文归档/` is evidence storage rather than disposable cache. Do not delete raw source snapshots merely because derived Markdown or text exists; clean it only through the archive retention and copyright-review process.
- Before any cleanup, confirm the target is outside the active Git worktree or intentionally tracked, check references and exact duplicates, then verify `git status -sb` after the operation. Never delete `.git`, active `.tmp` review artifacts, or source records by broad pattern alone.

## 图片检查与视觉自由

- 图片不设固定比例、尺寸、配色、构图、布局、字体、图标、Logo 或生成流程；是否使用官方素材、自定义视觉、UI 示意图或纯文字版式按任务决定。
- 只保留三类硬检查：图片文件能否打开、文章引用的本地文件是否存在、素材是否有明确的来源/许可或存在明显的伪造官方风险。
- 尺寸、比例、安全区、留白、文字大小、视觉节奏和手机预览只输出建议或供人工复核，不因偏离历史模板而阻断。
- 新图可以使用模型直接生成，也可以使用本地脚本、SVG、设计工具或其他经授权的视觉路径；生成方式不构成项目级规则。
## 正式文章编号规则

- 正式文章使用两位数编号，新稿使用 `07-资料与流程/文章资产登记表.md` 中当前最高正式编号加 1。下架、删除或转为草稿时，不自动重排以及不批量更名已发布文章。
- 只有负责人明确批准“一次性编号迁移”时，才允许重排。先在 `07-资料与流程/编号变更记录.md` 固化旧号→新号映射、涉及资产和验收标准，再执行。
- 一次性迁移必须同步正文、正在使用的图片、正文引用、元数据、资产登记表、README/索引、本地链接和发布记录，然后运行 `python 09-工具脚本/一键发布检查.py`。
- `07-资料与流程/文章资产登记表.md` 同时记录「入库状态」和「发布状态」；正式文章上线、修改或下架时先更新发布状态，再运行 `09-工具脚本/重建知识库索引.py` 同步 README 的每篇文章状态列。

## Codex Productivity Contract

- Run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1` for a lightweight verification; add `-Deep` before an authorized article release review.
- Versioned Git hooks live in `.githooks/`; run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-git-hooks.ps1` when configuring a checkout. `pre-commit` checks staged paths, secrets, and whitespace, while `pre-push` runs the verification entry point.
- Use the `github-update-push` workflow only when the user explicitly requests synchronization: inspect local changes, fetch, validate, stage explicit paths, push the authorized scope, and compare local/upstream/remote identities.
- `article-Skill` 仅在任务明确调用、项目明确锁定或需要复用其生产能力时使用。本项目不把 `article-Skill` 的风格、结构和视觉模板自动扩大为全局硬规则；其他经授权的生成路径也可以使用，但必须遵守事实、版权、安全、隐私和仓库完整性边界。不得静默发布。
- If using an agent, assign disjoint file ownership and require a final main-task review; do not parallel-edit the same article or lock file.
