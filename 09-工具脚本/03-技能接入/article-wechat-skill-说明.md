# article-Skill 项目接入说明

本项目可以按任务需要使用外部 canonical `article-Skill`，但不再在 `Codex_article` 内维护 Skill 的版本锁定文件、项目适配配置或历史快照。

## 当前接入方式

- canonical Skill：`D:\projects_git\article-Skill`
- 统一检查入口：`python 09-工具脚本/01-发布校验/文章统一检查.py --id <文章编号> --strict --skill-root ..\article-Skill`
- 项目级发布检查：`python 09-工具脚本/01-发布校验/一键发布检查.py`

统一检查会确认指定的 `article-Skill` 是 Git 工作区、包含文章包校验器且工作区干净，然后调用其当前版本执行文章包检查。检查不再比较项目内的固定 commit，也不从个人安装目录回退。

### 元数据兼容与本地预览

统一检查查找文章元数据时，优先使用集中登记的 `07-资料与流程/03-资产与核验/文章元数据/{文章编号}-*.json`；历史文章若尚未迁移集中元数据，则回退读取文章包内的 `article.json`。两处都不存在时才阻断。这样既不重新引入项目锁文件，也能让早期文章继续接受同一套严格检查。

如需先在本地查看文章排版，可生成临时 HTML 预览：

`python 09-工具脚本/01-发布校验/生成文章预览.py --article "<文章 Markdown 绝对路径>" --output ".tmp/preview/<文章编号>.html"`

预览文件只用于检查图片、链接、表格、代码块和窄屏阅读，不代表微信公众号或其他内容平台已经通过最终渲染验收。正式发布前仍应在可渲染页面中人工复核图片可见性、链接可点击性、手机端段落节奏和特殊字符。

## 版本与责任边界

- Skill 的版本、规则和 Git 历史由 canonical `article-Skill` 仓库自行维护。
- 本项目只维护文章正文、元数据、素材登记、索引和发布检查。
- Skill 工作区存在未提交改动时，统一检查会阻断，避免使用不可追溯的临时规则。
- 如果需要复现历史结果，应在 canonical Skill 仓库中使用对应 Git 提交，而不是在本项目新增锁文件或快照。

## 生成后的受控 GitHub 同步

生成器得到结果 JSON 后，可以调用：

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-generated-article.ps1 -ResultPath <生成结果.json> -Execute`

同步脚本的授权、目标分支、路径范围和安全检查由脚本内的固定安全契约执行，不依赖项目适配 JSON。它仍然要求明确的 `repository_sync_intent`，不会自动合并、强推、清理、stash 或代替人工平台发布。

不带 `-Execute` 时是无副作用干跑：

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-generated-article.ps1 -ResultPath <生成结果.json>`
