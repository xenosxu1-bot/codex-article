> 一句话结论：Codex Dream Skin 不是官方主题商店，而是一套给 Codex 桌面应用增加外观主题的本机工具；这篇文章更关注它的安装、验证和回滚流程，而不是单纯讨论界面好不好看。

如果你每天打开 Codex 写代码、整理文章、跑任务，默认界面用久了会有一种工具疲劳：功能很强，但工作区很像临时控制台。Codex Dream Skin 做的事很直接：给 Codex Desktop 加一层外部视觉皮肤，让首页更有氛围，同时尽量保留原生侧栏、项目选择、任务内容和输入框。

截至 2026 年 7 月 21 日，Fei-Away/Codex-Dream-Skin 在 GitHub 上约有 1.12 万个 star，最近一次推送在 2026 年 7 月 20 日。对读者来说，更值得关注的不是热度本身，而是它把换肤这件小事拆成了安装、启动、验证和回滚四个可检查步骤。

但这类工具也最容易被误解。它不是 OpenAI 官方产品，也不是把 Codex 改造成另一个应用。项目文档反复强调：不修改 WindowsApps、不替换 app.asar、不改官方签名；Windows 版本通过本机回环 CDP 给官方 Store 安装的 Codex 加载外部主题。

![Codex Dream Skin 能力地图](<../08-素材库/图片/正文插图/28-给 Codex 换一套皮肤：Codex Dream Skin 实操教程-正文插图01.png>)

## 先把它理解成四个能力

第一个能力是外观主题化。

它通过 CSS 和装饰 DOM 给 Codex 增加背景、层次、透明感和氛围。关键点是：真实侧栏、真实输入框、真实项目菜单仍然应该在上面工作，装饰层不能挡住按钮。

第二个能力是本机注入。

Windows 版本使用本机回环地址上的 Chromium DevTools Protocol，也就是 CDP。通俗说，它让本机工具连接到本机正在运行的 Codex 渲染页，把视觉层加进去。文档强调 CDP 端点应只绑定本机回环地址，并校验目标属于当前官方 Codex 包。

第三个能力是主题仓库。

它不是一次性贴图。Windows 版本会在 `%LOCALAPPDATA%\CodexDreamSkin` 下维护当前主题、保存主题、导入图片、日志和状态。用户可以通过系统托盘更换背景、保存当前主题、切换已保存主题、暂停或恢复皮肤。

第四个能力是可验证和可回滚。

这点比好看更重要。项目提供 verify 脚本生成截图并检查皮肤是否加载、原生侧栏和输入框是否存在、装饰层是否不拦截鼠标事件；也提供 restore 脚本恢复官方外观并关闭已保存的调试会话。

## Windows 用户的最小实操闭环

下面的流程按项目 Windows 文档和运行时说明整理，并已按 2026 年 7 月 21 日的仓库内容复核。为了不替读者改动本机 Codex，这里不把它包装成已在所有设备上实测成功的经历；你真正操作时，以仓库当前 README 和脚本为准。

![Windows 最小实操闭环](<../08-素材库/图片/正文插图/28-给 Codex 换一套皮肤：Codex Dream Skin 实操教程-正文插图02.png>)

### 第一步：确认前置条件

Windows 版本需要三样东西：

- 从 Microsoft Store 安装、且已注册到当前用户的官方 `OpenAI.Codex` 应用。
- Node.js 22 或更高版本，并且 `node.exe` 能从 `PATH` 找到。
- Windows PowerShell 5.1 或更高版本。

安装前要完全退出 Codex。普通使用不需要管理员权限，也不需要去接管 WindowsApps 目录。

### 第二步：下载仓库并进入 Windows 目录

> 下载仓库并进入 Windows 目录
> `git clone https://github.com/Fei-Away/Codex-Dream-Skin.git`
> `cd Codex-Dream-Skin\windows`

如果你已经下载过源码，先更新仓库，再进入 `windows` 目录。这个目录本身就像一个完整技能包：里面有 `SKILL.md`，也有 `scripts`、`assets`、`references` 和 `tests`。

### 第三步：安装一次

> 执行安装命令
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-dream-skin.ps1`

安装器会做几件事：校验官方 Codex Store 包和 Node.js，保存可恢复的外观配置，初始化本地主题仓库，并创建三个常用快捷方式：

- `Codex Dream Skin`：启动或重新应用皮肤。
- `Codex Dream Skin - Tray`：打开系统托盘主题控制。
- `Codex Dream Skin - Restore`：恢复官方外观并关闭已保存的 CDP 会话。

这里的 `Bypass` 只作用于这一次用户主动发起的安装过程。项目文档说明，日常快捷方式使用 `RemoteSigned`，不会绕过系统或企业组策略。

### 第四步：启动并验证

推荐从 `Codex Dream Skin` 快捷方式启动。命令行方式如下：

> 启动并提示重启 Codex
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dream-skin.ps1 -PromptRestart`

启动后，不要只看界面变漂亮就结束。继续运行验证：

> 执行验证命令
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-dream-skin.ps1 -ScreenshotPath "$env:TEMP\codex-dream-skin.png"`

验证脚本会确认几类关键事实：CDP 端点是否只绑定本机回环地址，当前渲染页是否加载预期版本皮肤，原生侧栏和输入框是否仍然存在，装饰层是否不拦截鼠标事件，首页主题结构是否正确加载。

这一步是很多换肤教程会跳过的部分，但它决定了这个工具能不能长期使用。**只要输入框、项目菜单或侧栏被挡住，视觉再好看也算失败**。

### 第五步：更换和保存主题

打开 `Codex Dream Skin - Tray` 后，可以更换 PNG、JPEG 或 WebP 背景图，保存当前主题，从已保存主题中切换，也可以暂停和恢复皮肤。

这里有一个很重要的图片规则：导入的图片必须是纯背景。不要把 README 截图、带窗口的效果图、带按钮的假界面、带文字的海报直接导入。项目文档给出的图片上限是 16 MB，宽或高不能超过 16384 像素，总像素不能超过 5000 万。

更稳妥的做法是先准备一张干净的 16:9 壁纸，只保留主体和背景，不要让图片里本身包含侧栏、输入框、Logo 或说明文字。这样 Codex 原生界面叠上去时，才不会出现双层 UI 和文字冲突。

### 第六步：会恢复，才算会安装

恢复官方外观的命令是：

> 恢复官方外观
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\restore-dream-skin.ps1 -RestoreBaseTheme -PromptRestart`

如果你还想删除 Dream Skin 创建的快捷方式，可以增加 `-Uninstall`：

> 恢复官方外观并删除快捷方式
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\restore-dream-skin.ps1 -RestoreBaseTheme -PromptRestart -Uninstall`

`-RecoverConfigBackup` 是更强的恢复动作，用于明确恢复安装前完整 `config.toml` 备份。它适合配置损坏、普通恢复无法解决时再用，不建议当作日常开关。

![验收与回滚清单](<../08-素材库/图片/正文插图/28-给 Codex 换一套皮肤：Codex Dream Skin 实操教程-正文插图03.png>)

## 它为什么适合写成 Codex Skill

Codex Dream Skin 值得拆开看的地方，是仓库里放了 `windows/SKILL.md`。这个 Skill 的名字是 `codex-dream-skin`，描述里写明了适用场景：当用户想给 Windows Codex 桌面应用应用、启动、验证、修复、更新或恢复完整装饰皮肤时使用。

这和 Codex Skills 的使用方式一致：Skill 是可复用工作流的作者格式，一个 Skill 目录包含 `SKILL.md`，也可以包含脚本和说明材料；Codex 可以根据用户显式提到的 Skill，或根据描述匹配任务来启用它。

也就是说，Codex Dream Skin 不只是一个工具项目，也是一份工作流说明书。它把容易漏掉的边界提前列出来：

- 不接管 WindowsApps。
- 不改官方可执行文件和签名。
- 安装前先关闭 Codex。
- 启动后必须 verify。
- 验收要看首页和普通任务页。
- 不用时用 restore 关闭调试会话。
- 背景图必须是无 UI 的纯壁纸。

如果你想让自己的 Codex 也能记住这套流程，不要只复制一段命令。更好的做法是保留完整技能目录：`SKILL.md`、`scripts`、`assets`、`references` 和 `tests` 要在同一个相对结构里。否则 Skill 读到了流程，却找不到脚本和检查项。

可以给 Codex 一张这样的任务卡：

> 任务卡示例：请按 Codex Dream Skin 的 Windows Skill 流程，帮我做一次只读检查：确认仓库目录、Node 版本、Codex Store 包状态、已有主题状态和可回滚路径。不要安装，不要启动，不要修改配置。先输出风险和下一步确认项。

这张任务卡的重点是先只读检查。等你确认风险，再让 Codex 执行安装、验证或恢复。这样更符合桌面工具的安全节奏。

## 安全边界：它可逆，但不是零风险

这类工具最容易被一句本机注入带偏。回环地址可以避免局域网访问，但 CDP 本身并不验证同一个 Windows 用户下的其他本机进程。项目文档也明确提醒：皮肤运行期间只运行可信本机软件，不用时执行 restore 关闭调试会话。

还有三条边界要记住。

第一，不要把换肤和 API 配置混在一起。项目 README 说明，换肤与 API 配置互相独立，不会自动改写模型供应商设置。看到所谓一键换肤顺便改 Key、改 Base URL 的脚本，要格外谨慎。

第二，不要把带人物、IP 或品牌元素的预设图直接当作可商用素材。仓库 README 也提醒，预设及效果图中的人物、IP 素材只作主题示意，商用或公开再分发前要自行确认肖像、素材和商标权利。本文没有搬运仓库效果图，也不建议直接把预设图当作可商用素材使用。

第三，不要在 Codex 更新后盲目复用旧路径。项目文档说明，脚本会动态发现当前 Store 包；更新后建议重新安装和启动，让受管运行时、快捷方式和包身份重新对齐。

## 适合谁，不适合谁

它适合三类人：

- 每天高频使用 Codex Desktop，希望把工作区做得更有氛围的人。
- 愿意按安装、验证、回滚流程操作，不把换肤当成随便点一下的人。
- 想学习如何把桌面工具封装成 Codex Skill 的开发者。

它不太适合三类人：

- 只想用官方默认外观，不想维护任何本机脚本的人。
- 不愿意看验证截图和恢复命令，只想追求视觉效果的人。
- 需要在企业受管设备上使用，但无法确认 PowerShell、Node、Store 包和安全策略的人。

所以，Codex Dream Skin 值得关注的不是某一张背景图，而是它把视觉改造做成了可检查、可恢复、可技能化的流程。先跑通最小闭环，再换自己的纯背景；先会 restore，再谈个性化。这样你得到的不是一次换肤尝鲜，而是一套可以长期维护的 Codex 桌面工作流。
