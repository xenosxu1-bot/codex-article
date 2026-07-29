# article-wechat Skill 项目接入说明

本项目不维护独立的文章视觉规则、封面提示词、通用检查器或封面渲染器。通用能力只由私有仓库 `article-Skill` 维护；项目内已清理 `09-工具脚本/article-wechat-skill/` 及所有独立规则副本，不作为新规则、脚本或运行时回退来源；追溯以 `article-Skill` 的 Git 历史为准。

## 当前接入方式

- 唯一版本锁定：`09-工具脚本/article-skill.lock.json`
- 项目适配配置：`09-工具脚本/article-skill-project.json`
- 统一检查入口：`python 09-工具脚本/文章统一检查.py --id <文章编号> --strict --skill-root ..\article-Skill`
- 项目级发布检查：`python 09-工具脚本/一键发布检查.py`

统一检查会验证指定的 `article-Skill` 是 Git 工作区、提交与锁定版本一致且工作区干净。个人安装目录 `~/.codex/skills/article-wechat` 不再作为项目检查的回退来源，项目内也不提供历史快照回退。

更新锁定版本的顺序：先在 `article-Skill` 完成验证、提交和推送，再更新本项目的 lock 文件；不得锁定未提交或未推送的规则。
