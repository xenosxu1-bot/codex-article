**14. Ollama + Open WebUI 新手教程：先把“本地 AI 助手”跑起来**

晚上十一点，你只是想问一句：冰箱里只剩鸡蛋、青菜和一把面，明早还要带孩子出门，能不能给我排个不折腾的早餐？

这类问题不一定值得打开一堆网页，也不一定适合把家庭信息、行程、病历截图、工作文档一股脑丢到云端。AI 真正进入生活，往往不是从“震撼演示”开始，而是从一个安静的小入口开始：你在自己电脑上打开一个网页，问它，改它，留下可复用的模板。

这篇只做一件事：用 **Ollama + Open WebUI**，先把一个能聊天、能帮你整理生活小问题的本地 AI 助手跑起来。

> 资料核验时间：2026-08-11。安装命令、镜像标签和版本信息以 Ollama 官方 README、Open WebUI 官方 Quick Start、GitHub Release 页面为准。本文不转载第三方博客截图；同类博文仅作为界面对照链接，发布版截图建议来自你自己的安装环境。

![Ollama 和 Open WebUI 的分工：Ollama 负责模型，Open WebUI 负责日常使用入口](<assets/figures/14-Ollama + Open WebUI 新手教程：先把“本地 AI 助手”跑起来-正文插图01.png>)

## 先说清楚：这不是“离线万能医生”

很多新手第一次听到“本地 AI”，会自动脑补三个词：免费、隐私、离线。

这三个词都要加条件。

- **本地运行**：模型主要在你的电脑上跑，常见聊天不必每句话都发给云端服务。
- **不是绝对隐私保险箱**：如果你把 Open WebUI 暴露到公网、装了插件、接了外部 API，数据边界就变了。
- **不是专业结论替代品**：法律、医疗、投资、用药、维修高压电器这类问题，只能让它帮你整理材料、列问题清单，不能当最终判断。

所以本文的目标很朴素：先让你有一个“家里能用的小助手”。它能帮你列菜单、整理旅行准备、改一封请假邮件、把说明书问题拆成检查清单。至于知识库、联网搜索、自动化工作流，等你先跑通这个入口再说。

## 1. 用一句话理解两个工具

**Ollama** 像一台本地模型发动机。它负责下载、运行和管理模型，比如 `qwen3:4b`、`llama3.2:3b`、`gemma3:4b`。官方 README 当前给出的入门方式，是安装 Ollama 后运行模型，并提供本地 REST API。

**Open WebUI** 像一个本地网页聊天界面。它把模型选择、聊天记录、用户界面、后续知识库能力放在一个浏览器入口里。官方文档把它定位为可自托管的 AI 平台，Quick Start 推荐 Docker 方式快速启动。

最小闭环是：

```text
浏览器里的 Open WebUI
        ↓
调用本机 Ollama
        ↓
本地模型生成答案
```

你可以先把它当成“家用 AI 记事本”：不追求一次搭成企业知识库，只追求今天能问、能改、能保存。

## 2. 安装前先做三项检查

别急着复制命令。新手最容易卡在这里：工具没错，是电脑环境没准备好。

### 电脑能不能跑？

如果只是体验，8GB 内存的电脑也可以试小模型，但会慢；16GB 内存会舒服很多。显卡不是必须，但有合适的 NVIDIA GPU 会更快。本文选择小模型，是为了让普通电脑先跑起来。

建议先从下面三个模型里选一个：

| 场景 | 模型示例 | 为什么适合新手 |
| --- | --- | --- |
| 中文生活问答 | `qwen3:4b` | 中文理解更稳，体积不算太大 |
| 英文资料摘要 | `llama3.2:3b` | 轻量，适合先验证流程 |
| 综合问答 | `gemma3:4b` | 容量适中，日常对话够用 |

模型名称不是本文发明的，均可在 Ollama Library 中检索。不同电脑速度差异很大，先选小的，别一上来下载几十 GB 的大模型。

### 要不要装 Docker？

Open WebUI 官方 Quick Start 推荐 Docker。对新手来说，Docker 的好处是少折腾依赖；坏处是第一次安装 Docker Desktop 可能要重启电脑，Windows 还可能涉及 WSL。

如果你只是想最快看到界面，按本文走：**本机安装 Ollama + Docker 运行 Open WebUI**。

### 哪些信息先不要放进去？

第一天先不要粘贴这些内容：身份证、完整病历、银行卡、公司内部文档、客户名单、密钥、Cookie、未脱敏日志。即使模型在本地跑，聊天记录、浏览器、插件和备份也会形成新的风险点。

## 3. 第一步：安装 Ollama

打开 Ollama 官方下载页，按你的系统安装。Windows 用户也可以使用官方 README 当前提供的 PowerShell 安装方式：

```powershell
irm https://ollama.com/install.ps1 | iex
```

如果你不习惯直接执行联网脚本，就用官网下载的安装包。安装完成后，打开 PowerShell，输入：

```powershell
ollama --version
```

能看到版本号，就说明 Ollama 命令已经可用。

接着下载并运行一个小模型：

```powershell
ollama run qwen3:4b
```

第一次会下载模型，时间取决于网络和模型大小。看到提示符后，可以先问一句：

```text
请用三句话解释：你现在是在我的电脑本地运行吗？有哪些事情不能保证？
```

这里不是为了考倒模型，而是让你建立第一条习惯：**先问边界，再问答案**。

如果你想确认服务是否在本机启动，可以试：

```powershell
curl http://localhost:11434/api/tags
```

能返回模型列表，说明 Ollama 的本地接口可访问。

## 4. 第二步：用 Docker 启动 Open WebUI

确认 Docker Desktop 已经启动后，打开 PowerShell，运行：

```powershell
docker run -d `
  -p 3000:8080 `
  --add-host=host.docker.internal:host-gateway `
  -v open-webui:/app/backend/data `
  --name open-webui `
  --restart always `
  ghcr.io/open-webui/open-webui:main
```

这条命令做了几件事：

- `-p 3000:8080`：把浏览器访问地址映射到 `http://localhost:3000`。
- `-v open-webui:/app/backend/data`：给 Open WebUI 一个持久化数据卷，避免容器重建后聊天记录和配置直接丢失。
- `--add-host=host.docker.internal:host-gateway`：让 Docker 容器能找到你电脑上运行的 Ollama 服务。
- `--restart always`：电脑重启或容器异常退出后尽量自动恢复。
- `ghcr.io/open-webui/open-webui:main`：使用官方文档中的主镜像标签。

Open WebUI 官方文档提醒：`:main` 和 `:latest` 都是跟随主分支滚动的镜像，不等同于最新稳定发布。如果你把它用于长期家庭资料库，建议后续改用版本标签，并保留备份和回滚方案。

启动后打开：

```text
http://localhost:3000
```

第一次进入时，按页面提示创建本地账号。进入聊天界面后，在模型选择处选择刚才下载的模型，例如 `qwen3:4b`。

## 5. 第三步：让它解决一个真实生活问题

别从“帮我改变人生”开始。先给它一件你今晚真的要处理的小事。

比如这个：

```text
你是一个只做家常方案的生活助理。
我家现在有：鸡蛋 4 个、青菜一把、挂面、牛奶、苹果。
明早 7:30 要出门，只有 20 分钟做早餐。
请给我 2 个方案：
1. 每个方案写出步骤和用时；
2. 不要推荐我没有的食材；
3. 最后列一个“前一晚可以提前准备什么”的清单。
```

你会发现，本地模型不一定比云端大模型聪明，但它很适合帮你把脑子里的杂事摆平：有什么、限制是什么、先做哪一步、最后检查什么。

再试一个适合工作和生活交界的任务：

```text
请帮我把下面这段话改成一封礼貌但不卑微的请假邮件。
背景：孩子明天上午要去医院复查，我需要请半天假。
要求：
- 语气自然，不要像模板；
- 不要透露具体病情；
- 结尾说明我会提前交接今天的待办。
原文：明天上午有点事，请假半天。
```

这就是本地 AI 助手最适合新手的起点：不碰敏感全文，不求神奇结论，只让它把你的表达变清楚。

![把第一个生活问题拆成可执行任务卡：输入事实、限制、输出格式和验收方式](<assets/figures/14-Ollama + Open WebUI 新手教程：先把“本地 AI 助手”跑起来-正文插图02.png>)

## 6. 把“会问”变成一个小模板

等你跑通以后，建议在 Open WebUI 里固定保存几类提示词。不是为了收藏更多 Prompt，而是让家里常见问题有一个稳定入口。

### 家庭菜单模板

```text
请根据我已有食材安排一餐。
已有食材：
时间限制：
人数：
不吃/过敏：
输出要求：给 2 个方案，每个方案包含步骤、用时、替代食材和最后检查清单。
```

### 出门准备模板

```text
请帮我做一份出门前检查清单。
目的地：
同行人员：
天气：
交通方式：
特殊限制：
输出要求：按“证件/衣物/药品/电子设备/路上安排/容易忘的事”分组。
```

### 说明书排障模板

```text
我会贴一段公开说明书内容，请只根据我提供的信息整理排障步骤。
设备：
故障现象：
我已经尝试过：
安全限制：不要建议拆机、强电操作或绕过安全保护。
输出要求：先列低风险检查，再列需要找售后的情况。
```

这三个模板不花哨，但很管用。你真正要训练的不是模型，而是自己的提问方式：先给事实，再给限制，最后说清楚输出长什么样。

## 7. 常见卡点：新手最容易在这五处摔跤

### 卡点一：Open WebUI 打不开

先看 Docker 容器是否在跑：

```powershell
docker ps
```

如果没有 `open-webui`，查看日志：

```powershell
docker logs open-webui
```

端口冲突时，把 `3000:8080` 改成 `3001:8080`，然后访问 `http://localhost:3001`。

### 卡点二：界面里没有模型

先确认 Ollama 本机有模型：

```powershell
ollama list
```

如果列表为空，回到 PowerShell 运行：

```powershell
ollama run qwen3:4b
```

如果有模型但 Open WebUI 看不到，通常是容器连接不到主机 Ollama。检查你是否加了：

```text
--add-host=host.docker.internal:host-gateway
```

必要时在 Open WebUI 的连接设置里确认 Ollama 地址指向本机服务。

### 卡点三：回答很慢

先别怀疑自己装错了。小模型、CPU、内存、磁盘、首次加载都会影响速度。处理方式很简单：换更小模型，关掉其他占内存的软件，少让它一次写长文。

### 卡点四：它一本正经地胡说

本地不等于正确。生活建议也要验收。你可以追加一句：

```text
请把上面的回答分成“确定事实”“你的推断”“需要我再确认的信息”。
```

这句话能过滤掉不少看似流畅的废话。

### 卡点五：想给全家或同事用

先别急着开公网。家庭局域网共享也要想清楚：谁能访问、谁能看聊天记录、是否有儿童使用、是否会上传敏感文档。Open WebUI 的开源许可证还对品牌修改有特定条件，团队或商业部署前要重新阅读 LICENSE 和官方企业说明。

## 8. 实图怎么配，才不侵权

这类教程最需要实图，但也最容易踩坑。很多博文会放 Open WebUI 的界面截图、Docker 命令截图、模型选择截图。它们可以帮你确认“我看到的界面是不是类似”，但不代表你可以把图下载下来放进自己的文章。

本文的处理方式是：

1. 正文里的两张图是原创信息图，只解释安装路线和任务卡，不伪装成官方界面。
2. 工具实图建议由发布者在自己的电脑上完成安装后截图：一张 `http://localhost:3000` 的模型选择界面，一张第一轮生活问答结果。
3. 同类博文只保留外链作为读者对照，不复制、不裁剪、不去水印、不改造成“自有截图”。

可作为界面对照的同类文章（只看界面走向和截图类型，不复制图片、不沿用未核实结论）：

- LLM Configurator：[Open WebUI + Ollama Complete Setup Guide (2026)](https://llmconfigurator.com/en/guides/open-webui-ollama-setup)，可对照 Docker 启动、首次打开和模型选择截图。
- Inkeybit：[Open WebUI: The Best Chat Interface for Ollama in 2026](https://www.inkeybit.com/blog/open-webui-ollama-guide)，可对照模型切换、聊天历史和设置界面；其中版本与许可证描述需以官方仓库为准。
- AIToolDiscovery：[Set Up Open-WebUI with Ollama: Local Chat Guide (2026)](https://www.aitooldiscovery.com/how-to/setup-open-webui-ollama)，可对照本地聊天界面和常见配置项。

如果要在公众号正文里放真正的工具截图，最稳妥的做法是：自己安装、自己截图、隐藏用户名和本机路径，图注写清“自建环境截图”。

## 9. 今天做到哪一步就够了？

如果你是 AI 新手，今天不要追求“全功能”。完成下面四件事就可以停：

- PowerShell 里能运行 `ollama list`。
- 浏览器能打开 `http://localhost:3000`。
- Open WebUI 里能选择一个本地模型。
- 它能帮你完成一件真实小事，比如早餐方案、请假邮件、出门清单。

跑通之后，你会更清楚自己要不要继续折腾：要知识库，就学 AnythingLLM 或 Open WebUI 的文档能力；要自动化，就学 n8n；要多模型和团队协作，再考虑更复杂的部署。

先别把 AI 想得太远。让它今晚帮你把明早的早餐安排好，就已经是一个不错的开始。

## 参考资料与核验入口

- Ollama 官方 README：https://github.com/ollama/ollama
- Ollama Quickstart：https://docs.ollama.com/quickstart
- Ollama API 文档：https://docs.ollama.com/api
- Ollama Library qwen3:4b：https://ollama.com/library/qwen3%3A4b
- Open WebUI 官方 Quick Start：https://docs.openwebui.com/getting-started/quick-start/
- Open WebUI GitHub README：https://github.com/open-webui/open-webui
- Open WebUI LICENSE：https://github.com/open-webui/open-webui/blob/main/LICENSE
- GitHub Release 核验：Ollama `v0.32.7`（2026-08-10 发布），Open WebUI `v0.11.0`（2026-07-27 发布），核验时间 2026-08-11。
