> 一句话结论：Hermes Agent 新手上手不要从 Gateway、MCP、Skills、语音和自动化一起开局，而是先按 **安装 → 选模型 → 跑通第一轮对话 → 验证会话恢复 → 再扩展工具** 的顺序，做出一个能稳定回复、能排错、能逐步加能力的最小闭环。

如果你最近在看开源 AI Agent，很容易被 Hermes Agent 的功能列表吸引：终端对话、TUI、消息网关、工具集、Skills、记忆、MCP、Cron、Telegram 或 Slack 入口、远程运行、团队协作，甚至还有面向研究的轨迹生成能力。

但新手最容易犯的错也在这里：还没确认模型能正常回复，就急着接 Telegram；还没理解工具权限，就打开一堆执行能力；还没跑通本机 CLI，就开始配置长期运行的云服务器。结果不是 Agent 不强，而是排错链条太长。

本文基于 [NousResearch/hermes-agent 官方仓库](https://github.com/NousResearch/hermes-agent) 和 [Hermes Agent 官方 Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) 文档，截至 2026-07-20 的公开信息整理。它不是深度源码解读，而是一份给新手的快速上手教程：先跑起来，再知道下一步该加什么。

下图是官方文档中的模型设置页。左侧用于在会话、模型、Skills、配置等模块间切换；主区域用于查看当前模型、用量和设置。官方示例界面为英文，本文把它当作功能位置参考，实际配置以你安装版本中的页面为准。

![Hermes Agent 官方 Web UI 模型设置实图](<../08-素材库/图片/正文插图/29-Hermes Agent 新手快速上手：从安装到跑通第一个 Agent-正文插图01.png>)


## 先用一句话理解 Hermes Agent

Hermes Agent 是 Nous Research 开源的自进化 AI Agent 项目。官方 README 对它的定位很明确：它不是只提供一个聊天窗口，而是把模型、工具、会话、技能、记忆、消息入口和自动化组合成一个可以长期运行的个人或团队 Agent。

如果你只想偶尔问几句 AI，直接用网页聊天工具就够了。Hermes Agent 更适合这些需求：

- 想在终端里让 AI 帮你读项目、跑命令、整理文件。
- 想把 AI 助手接到 Telegram、Discord、Slack、WhatsApp、Signal 等消息入口。
- 想把常用流程沉淀成 Skills，后续反复调用。
- 想配置不同模型供应商，而不是被单一模型入口锁死。
- 想把 Agent 放在一台长期运行的机器上，逐步接入自动化任务。

官方 README 提到，Hermes Agent 支持多种模型或端点，包括 Nous Portal、OpenRouter、NVIDIA NIM、MiMo、z.ai/GLM、Kimi/Moonshot、MiniMax、Hugging Face、OpenAI 和自定义端点。也就是说，它更像一个 Agent 工作底座，而不是一个固定模型客户端。

新手先记住一个原则：**先证明它能稳定完成普通对话，再逐层打开 Gateway、Cron、Skills、MCP 和远程运行能力**。

## 安装前准备：别让第一步卡在环境上

开始之前，先确认三件事。

第一，系统平台。官方 README 写明，安装脚本支持 Linux、macOS、WSL2 和 Android Termux；Windows 用户可以使用 PowerShell 安装命令，也可以优先考虑 Hermes Desktop 安装器。

第二，模型来源。官方 Quickstart 把选择 Provider 视为最重要的设置步骤。你可以走 Nous Portal 的 OAuth 快捷路径，也可以选择 OpenAI、OpenRouter、GitHub Copilot、Qwen OAuth、xAI Grok OAuth、本地或自托管 OpenAI-compatible endpoint 等路径。不同 Provider 的登录方式、密钥和模型名不同，先选一种稳定方案，不要一开始做多 Provider fallback。

第三，排错心态。Hermes Agent 是开源 Agent 工具，功能强，但也意味着安装、依赖、网络、模型权限、系统终端和工具调用都可能成为变量。新手不要把第一次目标设成自动化万事屋，第一次目标只设成：能打开、能回复、能恢复会话。

![Hermes Agent 新手最小闭环流程图](<../08-素材库/图片/正文插图/29-Hermes Agent 新手快速上手：从安装到跑通第一个 Agent-正文插图04.png>)


## 第一步：安装 Hermes Agent

如果你使用 macOS 或 Windows，官方 Quickstart 推荐优先从 Hermes 官网下载 Desktop installer，安装命令行和桌面应用。对于只想使用命令行的用户，也可以按官方脚本安装。

Linux、macOS、WSL2 或 Termux 的命令是：`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`。

Windows PowerShell 的命令是：`iex (irm https://hermes-agent.nousresearch.com/install.ps1)`。

安装完成后，Linux 或 macOS 用户通常需要重新加载 shell，例如运行 `source ~/.bashrc` 或 `source ~/.zshrc`。Windows 用户安装完成后，如果命令不可用，先关闭并重新打开终端，再运行 `hermes`。

这里建议新手做一个小检查：不要立刻配置所有功能，只确认终端能识别 `hermes` 命令。如果命令不存在，优先处理 PATH、终端重启和安装目录问题，而不是继续往下乱改配置。

## 第二步：选择模型和 Provider

安装只是把工具放进系统里，真正决定 Hermes 能不能回复的是 Provider 与模型配置。

官方 Quickstart 建议使用 `hermes model` 交互式选择 Provider 和模型。如果你选择 Nous Portal，可以按官方文档使用 `hermes setup --portal` 走 OAuth 快捷路径；如果你选择其他模型供应商，就按对应路径准备 API Key、OAuth 登录或自定义 endpoint。

新手这里不要追求一次配置全家桶，只做三件事：

1. 选一个你确定可用的 Provider。
2. 选一个当前账户有权限调用的模型。
3. 保存配置后立刻做一次普通对话测试。

如果 Hermes 打开了，但回复为空、报错或行为异常，优先重新运行 `hermes model`，确认 Provider、模型名和认证方式。不要先怀疑 Skills、MCP 或 Gateway，因为基础模型链路不通时，后面的能力都无法稳定工作。

## 第三步：跑通第一次对话

官方 Quickstart 给了两个入口：`hermes` 启动经典 CLI，`hermes --tui` 启动现代 TUI。两者共享会话、斜杠命令和配置，新手可以先用 `hermes`，想要更现代的终端界面再试 `hermes --tui`。

第一次对话不要写复杂需求。建议用这类容易验收的任务：

- 用 5 个要点总结当前目录看起来是什么项目。
- 查看当前目录，告诉我最可能的入口文件是什么。
- 帮我列一个干净的 GitHub PR 工作流。

这些任务有共同点：目标清楚、结果容易验证、必要时可以调用低风险工具。你能判断它有没有读到正确目录，也能判断它是不是在瞎编。

第一次成功的标准不是回复很长，而是这四件事都成立：

- 欢迎界面能显示你选择的模型或 Provider。
- Agent 能正常回复，没有认证或模型不可用错误。
- 如果任务需要，它能调用低风险工具并返回结果。
- 第二轮继续追问时，上下文没有立刻断掉。

只要这个最小对话成立，你就已经越过新手阶段最关键的一关。

## 第四步：验证会话能恢复

很多人第一次试 Agent 只看它能不能答一句话，但长期使用更重要的是会话能不能保存和恢复。官方 Quickstart 建议在继续扩展前验证 resume。

你可以运行 `hermes --continue`，也可以用短命令 `hermes -c`。它应该回到刚才的会话。如果找不到旧会话，可能是你切换了 profile，或者之前会话没有保存成功。

为什么这一步重要？因为后面你一旦接入消息网关、长期任务、远程机器或团队入口，排错会更依赖会话记录。如果会话恢复本身不稳定，你很难判断问题来自模型、配置、平台入口还是历史上下文。

我的建议是：每次换 Provider、换机器或升级 Hermes 后，都先做一次对话和恢复验证，再去改更多设置。

## 第五步：再打开 Skills、工具和 MCP

当基础聊天稳定之后，才进入 Hermes Agent 真正有意思的部分。

官方文档把 Skills 描述为按需加载的指令文档。每个 Skill 是一个 `SKILL.md` 文件，包含名称、描述和步骤。Hermes 会先读取简短描述，只有任务需要时才加载完整内容，这样不会让每次请求都塞满上下文。

你可以用 `hermes skills browse` 浏览可用 Skills，用 `hermes skills search kubernetes` 这类命令按关键词搜索，用 `hermes skills install openai/skills/k8s` 安装某个 Skill。安装流程会先进行安全扫描；扫描通过不代表每个外部 Skill 都适合你的权限边界，仍要先看来源、步骤和它可能调用的工具。

下图是官方 Skills Hub 截图。左侧是导航，中间列出可浏览和筛选的技能；新手实际操作时，先预览来源和权限，再安装一个明确需要的 Skill，不要因为功能多而批量添加。官方示例界面为英文，关键操作已在上文用中文说明。

![Hermes Agent 官方 Skills Hub 实图](<../08-素材库/图片/正文插图/29-Hermes Agent 新手快速上手：从安装到跑通第一个 Agent-正文插图02.png>)


工具与 MCP 则负责扩展执行能力。新手不要一次性全开，建议按风险从低到高启用：

1. 只读能力：帮助检索、总结、查看目录、读取指定文件。
2. 可回滚能力：生成草稿、整理资料、创建临时文件。
3. 执行能力：运行命令、改项目、连接外部服务。
4. 长期自动化：Cron、Webhook、消息网关、团队入口。

这套顺序的目的不是保守，而是让你每次只增加一个变量。出错时，你才知道该回到哪一步。

## 第六步：需要手机或团队入口时，再配置 Gateway

Hermes Agent 的一个重要能力是 Messaging Gateway。官方文档提到，它可以连接 Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant、Microsoft Teams 等入口。

但请记住，Gateway 不是第一步。只有当 CLI 已经稳定工作后，再运行 `hermes gateway setup` 完成平台配置；按向导确认后启动 Gateway，才更容易把问题定位在模型、平台还是权限设置。

如果你只是个人使用，建议先接一个私聊渠道，比如 Telegram 或 Discord 私聊；如果你要放进团队群，先设计好谁能使用、能调用哪些工具、是否允许写文件、是否需要命令审批。Agent 进群以后，不是所有消息都应该触发执行，也不是所有人都应该拥有相同权限。

下图是官方 Kanban 工作台示例。它把任务按状态放进不同列，适合跟踪持续任务；但它不是首次安装必须开启的功能。官方示例界面为英文，先把 CLI 与会话恢复跑稳，再考虑这类协作视图。

![Hermes Agent 官方 Kanban 工作台实图](<../08-素材库/图片/正文插图/29-Hermes Agent 新手快速上手：从安装到跑通第一个 Agent-正文插图03.png>)


## 新手最容易踩的 7 个坑

### 1. 模型没通，就开始配一堆工具

现象是界面能打开，但回答异常、空回复或不断报错。优先重新运行 `hermes model`，确认 Provider、模型名、认证方式和账户权限。

### 2. 直接追求多 Provider fallback

多 Provider 很适合长期稳定性，但不适合第一天。先让一个 Provider 稳定，再考虑 fallback，否则你不知道错误来自哪个模型链路。

### 3. 把执行权限开得太早

文件写入、命令执行、浏览器操作和外部平台发送都属于高风险能力。新手先用只读工具，等能看懂工具调用记录后，再启用执行能力。

### 4. CLI 没跑通就接 Gateway

消息平台多一层 token、allowlist、平台回调和用户身份，排错复杂度会明显上升。先本机 CLI，后 Gateway。

### 5. 忽略会话恢复

能回答一次不等于能长期使用。`hermes --continue` 或 `hermes -c` 能恢复上一轮，会让后续排错轻很多。

### 6. 把 Skills 当插件市场乱装

Skills 的价值是沉淀稳定流程，不是越多越好。先安装和当前任务直接相关的 Skills，用完后观察是否真的提升交付质量。

### 7. 没有给 Agent 明确验收标准

别只说帮我看看这个项目。更好的说法是：先读 README 和配置文件，判断项目语言、启动入口、测试命令和潜在风险，最后给我一个不超过 8 条的上手清单。这样 Agent 的输出更容易被你检查。

## 一套适合新手的 30 分钟练习

如果你想今天就上手，可以按下面这套节奏走。

### 前 10 分钟：安装和模型

完成安装，打开新终端，确认 `hermes` 命令可用。然后运行 `hermes model` 或 `hermes setup --portal`，只选择一个你确定能用的模型入口。

### 第 10 到 20 分钟：第一次可验证对话

在一个你熟悉的项目目录里启动 Hermes。让它做一件容易判断的事，比如总结目录结构、找入口文件、列运行命令。不要让它直接修改项目。

### 第 20 到 30 分钟：恢复会话和低风险工具

运行 `hermes -c` 恢复刚才的会话。继续让它读取同一个项目里的 README 或配置文件，输出一份上手清单。只要它能恢复上下文，并且输出与你的项目事实相符，这次练习就合格。

下一步再考虑 Skills、MCP、Gateway 或长期自动化。不要把所有高级能力塞进第一次体验里。

## 可复用的新手任务卡

你可以直接把下面这段改成自己的项目任务：

> 请先只读当前项目，不要修改任何文件。按顺序完成：1. 判断项目类型和主要语言；2. 找出最可能的启动入口；3. 找出测试、构建或检查命令；4. 说明哪些结论来自文件证据，哪些只是推断；5. 最后给我一份 8 条以内的新手上手清单。

如果这张任务卡能跑通，再换成更复杂的任务卡：

> 请根据当前项目的 README 和配置文件，为一个新成员写一份 30 分钟上手路线。要求包含环境准备、首次启动、验证命令、常见错误和不要做的危险操作。先只输出计划，不执行命令。

这类任务最适合用来训练你和 Agent 协作，因为它同时考察信息读取、结构化表达、边界说明和验收标准。

## 最后给新手的使用建议

Hermes Agent 的价值不在于第一天就把所有功能打开，而在于你能把它逐步变成自己的 Agent 工作台。

第一天只追求三件事：能安装、能回复、能恢复会话。第二天再加低风险工具和 Skills。等你能看懂它每次为什么调用工具、输出能否被验证，再接入 Gateway、Cron、MCP 和团队入口。

如果你按这个顺序上手，Hermes Agent 就不会是一堆让人眼花的功能名，而会变成一条清楚的路线：先会对话，再会使用工具，最后才成为可长期运行的 AI 助手。
