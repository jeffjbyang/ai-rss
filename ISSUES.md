# 每日 AI 技术简报 MVP Issues

这些 issue 从 `AI_TECH_BRIEF_PRD.md` 拆解而来，按依赖顺序排列。每个 issue 都是一个可独立验证的垂直切片，优先保证 MVP 能端到端跑通。

## Issue 1: 最小采集到候选闭环

## What to build

构建最小可运行链路：系统读取源配置，从 1-2 个 RSS 源采集内容，写入本地 SQLite，并生成当天候选 Markdown 与 JSON 文件。完成后，应能在没有飞书、没有 LLM 的情况下，看到候选内容从源头进入本地归档。

## Acceptance criteria

- [ ] 支持从 `sources.yaml` 读取 RSS 源配置。
- [ ] 支持采集至少 1-2 个 RSS/Atom 源并解析标题、链接、发布时间、摘要或正文片段。
- [ ] 支持将采集结果写入 SQLite。
- [ ] 支持生成 `candidates/YYYY-MM-DD.md` 和 `candidates/YYYY-MM-DD.json`。
- [ ] 重复运行不会为同一 URL 创建重复候选。
- [ ] 提供一条本地命令，可手动运行并验证完整链路。

## Blocked by

None - can start immediately

---

## Issue 2: 飞书 Markdown 推送闭环

## What to build

构建从最终 Markdown 简报到飞书群机器人的推送链路。系统读取 `briefs/YYYY-MM-DD.md`，通过飞书 webhook 发送消息，并记录推送成功、失败和重试日志。

## Acceptance criteria

- [ ] 支持通过环境变量配置飞书 webhook。
- [ ] 支持读取 `briefs/YYYY-MM-DD.md` 并推送到飞书群。
- [ ] 飞书 webhook 未配置时给出清晰错误，不泄露敏感信息。
- [ ] 推送失败时至少重试一次，并记录失败原因。
- [ ] 提供一条本地命令，可用测试 Markdown 验证推送。

## Blocked by

- Issue 1: 最小采集到候选闭环

---

## Issue 3: 日报窗口与定时运行

## What to build

实现日报的时间窗口和定时运行规则：每天北京时间 17:50 生成候选和默认最终简报，18:10 推送过去 24 小时的内容，即前一日 18:10 到当日 18:09。

## Acceptance criteria

- [ ] 支持按北京时间计算日报日期和过去 24 小时时间窗口。
- [ ] 候选生成只包含窗口内内容；发布时间缺失时使用首次采集时间。
- [ ] 支持生成默认 `briefs/YYYY-MM-DD.md`。
- [ ] 提供 cron 配置示例，包含 17:50 生成和 18:10 推送。
- [ ] 本地可用命令模拟指定日期和时间窗口。

## Blocked by

- Issue 1: 最小采集到候选闭环
- Issue 2: 飞书 Markdown 推送闭环

---

## Issue 4: P0 官方 RSS/博客采集

## What to build

扩展采集源，覆盖第一批 P0 官方 AI 技术信息源。系统应优先使用 RSS/Atom；没有稳定 RSS 的源可以先保留在配置中但标记为待实现，不阻塞整体任务。

## Acceptance criteria

- [ ] 在源配置中加入第一批 P0 官方源。
- [ ] 至少成功采集 OpenAI、Anthropic、Google DeepMind、Meta AI、Microsoft、NVIDIA、AWS、Hugging Face 中可用的公开 RSS/Atom/博客源。
- [ ] 每个源记录名称、类型、优先级、标签、URL 和启用状态。
- [ ] 单个源采集失败不影响其他源。
- [ ] 采集日志能看出每个源的成功、失败和候选数量。

## Blocked by

- Issue 1: 最小采集到候选闭环

---

## Issue 5: GitHub 趋势与 Release 采集

## What to build

接入免费 GitHub 数据能力，采集泛 AI 技术、AI coding、Agentic Coding、软件交付实践相关 repo 的趋势信号和 release 信息。GitHub 模块应有个性化加权，但不局限在既有关注圈。

## Acceptance criteria

- [ ] 支持配置关注 repo 列表和关键词查询。
- [ ] 支持采集 repo 基础信息、star 数、更新时间、描述、topic 和最新 release。
- [ ] 支持记录短期增长相关字段；无法直接获取时记录可用替代信号。
- [ ] AI coding / 软件交付相关 repo 能被识别并打标签。
- [ ] 泛 AI/LLM/Agent/RAG/多模态/推理部署/开发工具相关 repo 也能进入候选池。
- [ ] GitHub API 失败或限流时不会阻塞其他采集源。

## Blocked by

- Issue 1: 最小采集到候选闭环

---

## Issue 6: arXiv / HN / 社区轻量采集

## What to build

接入研究和社区轻量采集能力，覆盖 arXiv、Hacker News 等免费公开源，为论文、研究突破和探索性内容提供候选。

## Acceptance criteria

- [ ] 支持 arXiv 查询，至少覆盖 AI、LLM、软件工程 Agent、Agent、RAG、多模态相关关键词。
- [ ] 支持 Hacker News 公开源或搜索结果采集。
- [ ] 采集结果写入统一候选数据结构。
- [ ] 研究内容能标记为论文/研究栏目候选。
- [ ] 社区内容能记录来源、标题、链接、时间和基础热度信号。
- [ ] 单个社区源失败不影响整体日报。

## Blocked by

- Issue 1: 最小采集到候选闭环

---

## Issue 7: 去重、规范化与时间归档

## What to build

实现候选内容的规范化、去重和时间归档，降低重复内容进入日报的概率，并保证每条内容可追溯到来源和采集时间。

## Acceptance criteria

- [ ] 支持 canonical URL 归一化。
- [ ] 支持标题归一化和基础相似度去重。
- [ ] 支持 `published_at`、`collected_at`、`brief_date` 等时间字段。
- [ ] 同一 URL 重复采集不会生成重复候选。
- [ ] 明显相同标题/来源的重复内容会被合并或标记到同一 dedupe group。
- [ ] 候选与入选条目均可归档查询。

## Blocked by

- Issue 1: 最小采集到候选闭环
- Issue 4: P0 官方 RSS/博客采集
- Issue 5: GitHub 趋势与 Release 采集
- Issue 6: arXiv / HN / 社区轻量采集

---

## Issue 8: 规则评分与栏目分配

## What to build

实现基础规则评分和栏目分配，从候选池中自动筛出 10-15 条高价值内容，并按 Top 3、AI Coding、模型/API、开源项目、论文、国内动态等栏目生成默认日报。

## Acceptance criteria

- [ ] 实现 0-100 分规则评分。
- [ ] 评分包含来源权威性、技术影响、新颖性、传播信号、主题匹配度和可信度扣分。
- [ ] 支持生成 Top 3 候选。
- [ ] 支持将候选分配到 PRD 定义的日报栏目。
- [ ] 内容不足 10 条时不硬凑，仍能生成日报。
- [ ] 评分原因能被记录，便于后续调试和人工修正。

## Blocked by

- Issue 7: 去重、规范化与时间归档

---

## Issue 9: AI Coding / 软件交付偏好规则

## What to build

在保持“每日 AI 技术简报”大范围不变的前提下，加入个性化偏好规则，让 AI coding、Agentic Coding，以及 Harness 所代表的 AI + 软件交付工程实践在同等质量下优先入选。

## Acceptance criteria

- [ ] 建立 AI coding / Agentic Coding / 软件交付相关关键词和标签表。
- [ ] 对代码 Agent、repo 理解、自动 PR、自动修复、测试生成、代码审查、CI failure repair、AI-assisted CI/CD 等内容增加主题匹配分。
- [ ] Harness 不作为唯一目标，而作为 AI + 软件交付工程实践的代表性锚点。
- [ ] 默认日报优先尝试保留 3 条相关内容；当天高质量内容不足时可以少于 3 条。
- [ ] 相关条目包含“可落地启发”字段；非核心主题可省略。

## Blocked by

- Issue 8: 规则评分与栏目分配

---

## Issue 10: 探索性内容配额

## What to build

实现探索性内容入选机制，避免日报只强化既有兴趣。每天在 10-15 条中优先保留 1-2 条非当前主关注但高信号的 AI 技术内容。

## Acceptance criteria

- [ ] 支持识别探索性候选内容。
- [ ] 探索性内容至少满足增长明显、技术路线新、工程潜在连接、来源可信、可验证中的两个条件。
- [ ] 探索性内容可来自 GitHub、论文、官方博客、社区讨论等不同来源。
- [ ] 纯营销、无实物概念、单平台孤立热度、标题党和明显刷热度内容会被降权。
- [ ] 默认日报中尽量保留 1-2 条探索性内容；候选质量不足时可以不保留。

## Blocked by

- Issue 8: 规则评分与栏目分配

---

## Issue 11: Markdown 人工审核流程

## What to build

实现轻量半自动审核流程：17:50 生成候选文件和默认最终简报，用户可在 18:10 前编辑 Markdown；无人编辑时系统自动发送默认 Top 10-15。

## Acceptance criteria

- [ ] 生成 `candidates/YYYY-MM-DD.md`，包含候选列表、评分、来源和链接。
- [ ] 生成 `candidates/YYYY-MM-DD.json`，保留结构化候选数据。
- [ ] 生成默认 `briefs/YYYY-MM-DD.md`。
- [ ] 推送任务读取 `briefs/YYYY-MM-DD.md`，因此人工修改会被保留并发送。
- [ ] 文件缺失时有清晰错误或自动回退到默认生成逻辑。
- [ ] 审核流程不依赖 Web 后台。

## Blocked by

- Issue 2: 飞书 Markdown 推送闭环
- Issue 8: 规则评分与栏目分配

---

## Issue 12: 运行健康检查与 MVP 验收报告

## What to build

加入最低限度的运行健康检查、失败告警和验收数据记录，避免系统静默失败，并支持连续 7 天 MVP 验收。

## Acceptance criteria

- [ ] 每次运行记录采集数量、失败源、候选数量、入选数量和推送状态。
- [ ] 单个源失败不阻塞整份日报。
- [ ] 候选总数低于 5 条时发送飞书健康告警。
- [ ] P0 源大面积失败时发送飞书健康告警。
- [ ] 飞书推送失败有重试和日志。
- [ ] 支持生成或查看连续 7 天运行结果，用于验证 MVP 成功标准。

## Blocked by

- Issue 3: 日报窗口与定时运行
- Issue 11: Markdown 人工审核流程

---

# 后续迭代 Issues

以下 issue 不纳入 MVP，建议在 MVP 连续运行稳定后再做。

## Issue 13: 可插拔 LLM 摘要增强

## What to build

在无 LLM 可运行的基础上，增加可插拔 LLM provider，只对 Top 20-30 候选生成更好的中文摘要、关键变化、为什么重要和可落地启发。

## Acceptance criteria

- [ ] LLM provider 可通过配置启用或关闭。
- [ ] 未配置 LLM 时系统仍按基础规则生成日报。
- [ ] 只对 Top 20-30 候选调用 LLM，避免不受控成本。
- [ ] LLM 生成失败时回退到规则摘要。
- [ ] 生成结果保留来源链接和不确定性标注。

## Blocked by

- Issue 8: 规则评分与栏目分配

---

## Issue 14: FastAPI 审核页面

## What to build

用简单 Web 页面替代 Markdown 文件审核，支持候选勾选、排序、编辑摘要、预览和保存最终简报。

## Acceptance criteria

- [ ] 支持查看当天候选列表。
- [ ] 支持勾选入选、移除、排序和编辑字段。
- [ ] 支持保存为 `briefs/YYYY-MM-DD.md`。
- [ ] 支持预览飞书推送内容。
- [ ] 未使用 Web 页面时，原 Markdown 审核流程仍可工作。

## Blocked by

- Issue 11: Markdown 人工审核流程
