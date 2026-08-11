# article-wechat Skill 项目接入说明

本项目不维护独立的文章视觉规则、封面或正文插图提示词、图片路由、通用检查器或渲染器。通用能力只由私有仓库 `article-Skill` 维护；项目内已清理 `09-工具脚本/article-wechat-skill/` 及所有独立规则和图片执行链副本，不作为新规则、脚本或运行时回退来源；追溯以 `article-Skill` 的 Git 历史为准。

## 当前接入方式

- 唯一版本锁定：`09-工具脚本/03-技能接入/article-skill.lock.json`
- 项目适配配置：`09-工具脚本/03-技能接入/article-skill-project.json`
- 统一检查入口：`python 09-工具脚本/01-发布校验/文章统一检查.py --id <文章编号> --strict --skill-root ..\article-Skill`
- 项目级发布检查：`python 09-工具脚本/01-发布校验/一键发布检查.py`

统一检查会验证指定的 `article-Skill` 是 Git 工作区、提交与锁定版本一致且工作区干净。个人安装目录 `~/.codex/skills/article-wechat` 不再作为项目检查的回退来源，项目内也不提供历史快照回退。

更新锁定版本的顺序：先在 `article-Skill` 完成验证、提交和推送，再更新本项目的 lock 文件；不得锁定未提交或未推送的规则。


## 生成后的受控 GitHub 同步

本项目已将 canonical `article-Skill` 的 `repository_sync_intent.v1` 与 `github-update-push` 安全流程绑定。文章生产运行时不会直接执行 Git；只有 `production` 结果同时满足以下条件，项目适配器才允许自动执行同步：

1. 请求显式包含 `authorization.allow_repository_sync: true`；
2. 结果中的 `repository_sync_intent.status` 为 `ready`，并绑定最终文章包的 artifact ID 与 SHA-256；
3. 意图目标为 `codex-article/main`，列出本次文章、索引、元数据和资产等精确归属路径；
4. 当前工作区没有预先暂存内容、没有意图外改动，且本地与 `origin/main` 完全一致。

生成器得到结果 JSON 后，调用：

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-generated-article.ps1 -ResultPath <生成结果.json> -Execute`

适配器会重新执行严格文章检查、一键发布检查、项目深度验证、差异/暂存检查；检查可能更新的索引也会再次核对是否仍在意图归属范围内。它只暂存意图中声明的路径，随后提交、推送并用 `git ls-remote` 校验远端提交。任一条件不满足即输出 JSON `blocked`，不会自动合并、强推、清理、stash 或平台发布。

不带 `-Execute` 时是无副作用干跑，可用于检查结果意图：

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-generated-article.ps1 -ResultPath <生成结果.json>`
