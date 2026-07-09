# 微信公众号 Codex 教程交付包

本仓库整理了 6 篇公众号风格 Codex 中文教程稿，配套中文标注界面图，适合用于公众号、知识库、社群教程或 GitHub 项目说明。

内容结合 OpenAI Codex 官方使用指导、常见 AI 开发博主的实战经验，以及面向新手的上手路径设计，重点帮助读者快速理解 Codex 的功能边界、使用入口、提示词写法、权限安全、团队规范和高频工作流。

## 文章目录

| 序号 | 文章 | 适合读者 |
| --- | --- | --- |
| 01 | [Codex 新手上手：从界面到第一个高质量任务](./01-Codex新手上手：从界面到第一个高质量任务.md) | 第一次使用 Codex 的开发者 |
| 02 | [Codex 进阶提效：配置、权限、复用与自动化](./02-Codex进阶提效：配置权限复用自动化.md) | 已经跑通过基础任务，希望稳定提效的用户 |
| 03 | [Codex 实战案例：从失败测试到可验证修复](./03-Codex实战案例：从失败测试到可验证修复.md) | 想用 Codex 修 bug、跑测试、形成闭环的用户 |
| 04 | [AGENTS.md 深度模板：让 Codex 按团队规则工作](./04-AGENTS.md深度模板：让Codex按团队规则工作.md) | 团队项目维护者、技术负责人 |
| 05 | [Codex 安全使用指南：权限、网络、密钥与上线前检查](./05-Codex安全使用指南：权限网络密钥与上线前检查.md) | 关注权限、密钥、生产风险的团队 |
| 06 | [Codex 速查表：常用命令、提示词与工作流](./06-Codex速查表：常用命令提示词与工作流.md) | 想收藏模板、快速套用的读者 |

## 图片素材

图片位于 `images/`，均为中文标注图或公众号封面式配图：

| 图片 | 用途 |
| --- | --- |
| `01-codex-app-cn.jpg` | Codex App 主界面中文标注图 |
| `02-codex-cli-cn.jpg` | Codex CLI 中文标注图 |
| `03-codex-ide-cn.jpg` | IDE 扩展中文标注图 |
| `04-codex-browser-cn.jpg` | In-app Browser 中文标注图 |
| `05-codex-artifact-cn.jpg` | Artifact Viewer 中文标注图 |
| `06-codex-advanced-workflow-cn.jpg` | 进阶工作流组合图 |
| `03-case-cover-cn.jpg` | 实战修复案例封面图 |
| `04-agents-cover-cn.jpg` | AGENTS.md 模板封面图 |
| `05-security-cover-cn.jpg` | 安全使用指南封面图 |
| `06-cheatsheet-cover-cn.jpg` | 速查表封面图 |
| `07-debug-loop-cn.jpg` | Debug 闭环流程图 |
| `08-agents-template-cn.jpg` | AGENTS.md 规则结构图 |
| `09-safety-cn.jpg` | 权限与安全边界图 |
| `10-cheatsheet-cn.jpg` | 常用命令与提示词速查图 |

## 推荐阅读顺序

新手建议按 `01 -> 03 -> 06` 阅读，先跑通界面和任务，再掌握修 bug 闭环，最后收藏常用模板。

团队使用建议按 `02 -> 04 -> 05` 阅读，重点把权限、`AGENTS.md`、验证标准和安全规则固化下来。

## 使用建议

发布到公众号时，可将 Markdown 内容复制到编辑器，再按图片引用位置插入对应图片。图片文字颜色已做强化，适合用作文章首图、分节说明图或社群分享图。

如果后续形成固定发布流程，建议把“文章结构、配图风格、验证清单、发布前检查”沉淀为一个 Codex Skill，方便以后继续批量生成同类教程。
