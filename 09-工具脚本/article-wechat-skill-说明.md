# article-wechat Skill 使用说明

本项目的文章生产通用能力由私有仓库 `article-Skill` 统一维护。`09-工具脚本/article-wechat-skill/` 是历史快照，仅保留用于追溯，不能作为新增规则或脚本的维护入口。

## 当前接入方式

- 版本锁定：`09-工具脚本/article-skill.lock.json`
- 项目适配：`09-工具脚本/article-skill-project.json`
- 统一校验：`python 09-工具脚本/文章统一检查.py --id <文章编号> --strict`
- 项目级发布检查：`python 09-工具脚本/一键发布检查.py`

标准稿和深度稿均需在 `07-资料与流程/文章元数据/` 保存单篇 JSON 记录。该记录驱动封面、正文图片、来源、检查和发布状态的核验；`文章资产登记表.md` 继续作为项目汇总索引。
