# 输出契约

## 默认原则

- 默认不发布、不上传、不提交；只有用户明确要求发布时才进入 `publishing-github.md`。
- 使用 UTF-8；Markdown 内图片使用相对路径；正文不依赖外部 CSS 或平台专有 HTML。
- 所有面向用户的文件应放在任务产物目录，避免散落在临时目录。

## 最小草稿

```text
articles/NN-YYYY-MM-DD-<slug>/
└── README.md              # Markdown 正文
```

适用于：仅草稿、快速改写、用户尚未要求配图或发布。

## 完整生产包

```text
articles/NN-YYYY-MM-DD-<slug>/
├── README.md              # 可发布 Markdown 正文
├── brief.md               # 内容 Brief
├── titles.md              # 标题候选与评分
├── structure-map.md       # 标题承诺、首屏回应、H2 承接和结尾回收
├── source-ledger.md       # 来源台账
├── claim-ledger.md        # 关键断言台账
├── fact-check.md          # 真实性核验记录（内部，不写入正文）
├── cover-brief.md         # 封面主副标题、关键词卡片、视觉主体和禁用元素
├── inline-image-storyboard.md # 正文插图分镜、放置位置和图文承接
├── image-ledger.md        # 图片台账
├── de-ai-report.md        # 去 AI 化扫描与改写记录
├── format-report.md       # 移动端与微信兼容检查
├── qa-report.md           # 质检报告
├── publish-record.md      # 发布记录；未发布时标记“未发布”
└── images/                # 本地保存且已引用的图片
```

适用于：完整生产包、需要留存真实性核验和版权审计记录的文章。

## GitHub 发布格式

若目标仓库沿用顶层 `NN-*.md` 规则，发布阶段可将生产包中的 `README.md` 复制/转换为仓库要求的顶层文章文件；本地生产包结构不因此改变。具体规则见 `publishing-github.md`。

## 交付说明

交付时说明：文章路径、图片路径、是否已完成事实核查、是否已完成版权复核、是否发布、还有哪些待确认项。
