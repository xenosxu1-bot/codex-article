# Codex 安全使用指南：权限、网络、密钥与上线前检查

副标题：Codex 越能干，越要给它清晰边界。

![Codex 安全使用指南封面](images/05-security-cover-cn.jpg)

## 开篇

Codex 能读代码、改文件、运行命令、调用工具，还能在合适配置下联网或操作外部服务。能力越强，越需要清楚的安全边界。

安全使用 Codex 的核心不是“什么都不让它做”，而是让它在正确的权限里做正确的事，并且每一步都可审查、可回滚、可验证。

## 一、先理解三类权限边界

Codex 常见的工作边界可以粗略理解为三层：

![Codex 安全边界图](images/09-safety-cn.jpg)

| 模式 | 适合场景 | 使用建议 |
| --- | --- | --- |
| `read-only` | 项目调研、代码解释、风险审查 | 只读最安全，适合先让 Codex 看懂项目 |
| `workspace-write` | 日常开发、修 bug、补测试 | 推荐作为常规开发默认模式 |
| `danger-full-access` | 隔离环境中的可信自动化任务 | 谨慎使用，必须确认工作区和命令风险 |

如果你不确定该怎么选，优先用：

```text
workspace-write + 需要时审批
```

这样既能让 Codex 正常开发，又不会无限制操作整个系统。

## 二、审批策略：让高风险动作停下来

审批策略决定 Codex 什么时候需要先问你。

适合让 Codex 自动做的事：

- 读取项目文件。
- 搜索代码。
- 修改工作区文件。
- 跑项目内的测试、lint、typecheck。

适合要求确认的事：

- 删除大量文件。
- 安装新依赖。
- 修改系统目录。
- 访问网络或下载脚本。
- 推送到远程仓库。
- 执行数据库迁移或生产命令。

你可以在任务里直接写：

```text
可以在工作区内修改文件和运行测试。新增依赖、删除文件、联网下载、推送远程前必须先说明原因并等待确认。
```

这句话非常适合企业项目。

## 三、密钥保护：不要把秘密交给上下文

不要把这些内容直接贴给 Codex：

- API key。
- 数据库密码。
- 私钥。
- 生产 token。
- Cookie、Session、OAuth refresh token。
- 用户隐私数据原文。

正确做法：

```text
我已经在本地 .env 配置好 OPENAI_API_KEY。请只读取环境变量名，不要打印、保存或提交密钥值。
```

如果 Codex 需要修改示例配置，可以让它只写占位符：

```env
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=postgres://user:password@localhost:5432/app
```

提交前重点检查：

```bash
git diff
git status --short
```

如果你怀疑密钥被写进文件，立即轮换密钥，不要只从 Git 里删掉。

## 四、联网与外部服务：能不用实时权限就不用

Codex 有时需要查官方文档、拉依赖、访问 GitHub、读取 Issue 或调用 MCP 服务。这里的原则是：

- 官方文档可以查，但要优先使用可信来源。
- 项目依赖要锁版本，不要随意升级。
- 外部服务写操作前要确认。
- 涉及账号、权限、费用的操作要人工确认。

适合写进任务的约束：

```text
如果需要联网，请只查官方文档或项目指定链接。不要访问未知脚本，不要执行从网页复制的安装命令，除非先解释风险。
```

## 五、上线前检查清单

让 Codex 改完代码后，可以直接要求它按这个清单自查：

```text
请在提交前做安全检查：

1. git diff 中是否包含密钥、token、Cookie、私钥或真实用户数据。
2. 是否新增了依赖；如果新增，说明用途和替代方案。
3. 是否修改了权限、登录、支付、删除、迁移相关逻辑。
4. 是否有可能造成数据丢失或接口不兼容。
5. 是否运行了最小相关测试、lint、typecheck 或 build。
6. 如果有未验证项，请列出原因和建议验证方式。
```

这段提示词适合在合并前使用，尤其是团队协作项目。

## 六、危险任务要拆小

下面这些任务不要一次性丢给 Codex：

- “帮我重构整个鉴权系统。”
- “把数据库迁移到新结构。”
- “升级所有依赖到最新版。”
- “清理项目里没用的文件。”

更稳的做法是拆成阶段：

1. 只读调研，列出影响范围。
2. 输出计划，不改文件。
3. 先改一个最小路径。
4. 跑验证。
5. Review diff。
6. 再继续下一步。

对应提示词：

```text
这是高风险任务。第一步只做只读调研：列出影响范围、风险点、建议计划。不要修改文件。
```

## 七、团队项目建议写进 AGENTS.md

建议把这些安全规则写进 `AGENTS.md`：

```md
## Security rules

- Never print, store, or commit secrets.
- Do not modify auth, billing, deletion, or migration logic without calling out risk.
- Ask before adding dependencies, deleting files, or running network commands.
- Prefer smallest relevant verification over broad risky commands.
- Final response must include verification result and remaining risk.
```

这样每个 Codex 任务都会自动带上安全底线。

## 结尾

Codex 的安全感来自三件事：权限可控、改动可审、结果可验证。

当你把沙箱、审批、密钥、联网和上线检查都讲清楚，它就能在更大的任务里发挥价值，而不是变成一个让人不敢放手的黑盒。

