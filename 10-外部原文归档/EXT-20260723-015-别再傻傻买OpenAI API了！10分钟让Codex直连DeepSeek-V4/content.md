# 别再傻傻买OpenAI API了！10分钟让Codex直连DeepSeek-V4

不用OpenAI API，直接让Codex接入DeepSeek-v4！
核心原理：CC-Switch 在你的本机启动一个代理服务，把 Codex 发出的请求透明地转发给DeepSeek，然后把响应再回传给 Codex，整个过程几乎不需要写代码，小白也能10分钟跑通。
准备工作
在开始之前完成工具安装，新手推荐安装Desktop版本，操作更方便。
工具
获取方式
用途说明

Codex 桌面版
chatgpt官方下载：https://chatgpt.com/zh-Hans-CN/download/
AI编程工具

CC-switch
GitHub官方下载：https://github.com/farion1231/cc-switch/releases
模型切换与代理工具

DeepSeek API Key
DeepSeek平台获取：https://platform.deepseek.com/
模型调用凭证

第一步：配置CC-Switch——让Codex认识DeepSeek

CC-Switch的作用是帮Codex“记住”DeepSeek这位新朋友，以后调用起来不用重复填API key。
• 运行CC-Switch后，在主界面选择 Codex。

• 点击右侧区域，添加模型供应商

• 点击添加供应商后，选择DeepSeek

• 在下面的表单中填入DeepSeek API Key

• 记得开启本地路由映射,然后保存

• CC-Switch界面会提示我们开启路由，可以点击左上角的设置按钮进入设置页面开启

• 点击路由设置菜单，开启路由

• 然后选择 Codex，返回主界面确保DeepSeek配置状态为“使用中”

第二步：让Codex跑起来

• 完成CC-Switch的配置后，一定要重新启动Codex。

如果你的Codex界面底部显示“custom”，别担心，去Codex安装目录找到 .codex 文件夹，手动把custom全部改成你喜欢的模型名称（比如DeepSeek-v4-Pro）就行。
• DeepSeek V4 flash和pro特点与适用场景

模型
特点
适用场景

DeepSeek V4 flash
速度快、成本低
日常代码补全、简单问答

DeepSeek V4 pro
能力强，支持推理内容
复杂架构设计、多步推理

第三步：给Codex自定义桌面宠物

• 打开 Codex 桌面端，进入设置 → 外观 → 宠物，体验内置宠物

• 在Codex 顶部导航里的 Skills → 找到 Hatch Pet → 安装

Hatch Pet是 Codex 内置的宠物生成技能。你只需要用自然语言描述想要的动物、风格、气质，不需要自己画图、切图或者编辑配置文件它就会自动完成。
• 生成主视觉图

• 拆解出多种动作的动画帧

• 把文件放到正确的目录，让 Codex 能识别

Codex 生成完成后，回到宠物设置界面，点击“刷新宠物文件夹”。新宠物就会出现在列表里，如果刷新后没看到，可以先重启 Codex，再刷新一次。
如果你也对AI感兴趣，别忘了点赞、收藏、转发，让更多小伙伴一起上车！欢迎在评论区分享你的AI经验或技巧～
