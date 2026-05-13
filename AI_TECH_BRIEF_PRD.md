# 每日 AI 技术简报 PRD / MVP 技术方案

## 1. 项目定位

建设一个 0 新增预算的“每日 AI 技术简报”系统，自动跟踪国内外 AI 技术信息源，在每天北京时间 18:10 通过飞书群机器人推送过去 24 小时内最值得读的 10-15 条内容，最多 20 条。

系统面向有工程背景的技术人员，尤其服务于个人对 AI 技术变化、AI coding / Agentic Coding，以及 Harness 所代表的 AI + 软件交付工程实践的持续跟踪。

## 2. 核心目标

- 每天用 10-15 分钟掌握高价值 AI 技术变化。
- 优先发现可落地的技术、工具、工程实践，而不是泛泛新闻。
- 重点关注 AI coding、代码 Agent、自动 PR、自动修复、测试生成、代码审查、CI/CD AI、软件交付自动化。
- 保留一定探索性，避免只看熟悉领域。
- 在 0 新增预算下稳定运行。

## 3. 非目标

- 不做全网舆情监控。
- 不承诺 X、微信公众号、知乎、微博、小红书的全量稳定覆盖。
- 不做第一版复杂 Web dashboard。
- 不购买 Feedly Pro、Inoreader Pro、X API、微信数据服务、企业舆情系统。
- 不做受版权保护内容的大规模全文再分发。

## 4. 日报规则

- 发送时间：每天北京时间 18:10。
- 覆盖窗口：过去 24 小时，即前一日 18:10 到当日 18:09。
- 主渠道：飞书群机器人。
- 数量：每天 10-15 条，最多 20 条；内容不足时不硬凑。

推荐分栏：

1. Top 3 必读
2. AI Coding / 软件交付工程实践
3. 模型 / API / 平台更新
4. 开源项目与工具
5. 论文与研究
6. 国内动态

栏目不硬凑，当天无高质量内容可以省略。

## 5. 单条格式

```text
[标签] 标题
来源：来源名称
摘要：一句话说明发生了什么
关键变化：具体变化点
为什么重要：对技术、开发者、生态或工程实践的影响
可落地启发：仅 AI coding / 软件交付相关条目需要
链接：原文链接
```

正文使用中文，保留英文模型名、项目名、API 名、论文名和关键术语。传闻、二手消息、无法验证内容必须标注不确定性。

## 6. 信息源优先级

### P0：必须优先覆盖

- 官方博客/RSS：OpenAI、Anthropic、Google DeepMind、Meta AI、Microsoft、NVIDIA、AWS、Hugging Face 等。
- AI Coding / Agentic Coding：GitHub Blog/Changelog、Copilot、Codex、Claude Code、Cursor、Windsurf、Sourcegraph、JetBrains AI、GitLab、Harness、CodeRabbit、Devin/Cognition、Factory。
- 开源项目：Aider、OpenHands、SWE-agent、Continue、Cline/Roo Code、SWE-bench、Terminal-Bench 等。
- GitHub 趋势：泛 AI/ML/LLM/Agent/RAG/多模态/推理部署/开发工具相关 repo。
- arXiv / Papers with Code：只收可能影响工程实践、模型能力或工具生态的内容。
- Hacker News、Reddit、核心 Newsletter 和个人博客。

### P1：尽量覆盖

- 国内 AI 公司与大厂技术博客：DeepSeek、智谱、Moonshot、阿里/通义、腾讯/混元、百度/文心、字节火山、MiniMax、阶跃星辰等。
- 行业大咖博客、Newsletter、YouTube、X 公开内容。
- 国内技术社区和媒体的深度技术文章。

### P2：有限覆盖

- 微信公众号、知乎、微博、B站、小红书。
- 第一版只做重点白名单和人工补链，不承诺全量、实时、稳定。

## 7. 个性化偏好

不把简报改成垂直专项，仍然是 AI 技术简报；但在评分中偏向：

- AI coding / Agentic Coding
- 代码 Agent、repo 理解、自动 PR、自动修复
- 测试生成、代码审查 Agent、CI failure repair
- Harness 所代表的 AI + 软件交付工程实践
- AI-assisted CI/CD、发布自动化、开发者效率、软件工程智能

同时每天保留 1-2 条非当前主关注但高信号的探索性内容。

## 8. 重要性评分

每条候选内容按 0-100 分粗排：

- 来源权威性：0-25
- 技术影响：0-25
- 新颖性：0-15
- 传播信号：0-15
- 主题匹配度：0-15
- 可信度扣分：0 到 -20

入选参考：

- 80+：Top 3 候选
- 60-79：普通入选
- 40-59：候选池
- 40 以下：归档或丢弃

同等分数下，优先 AI coding / 软件交付工程实践相关内容；但不排斥其他高信号 AI 技术变化。

## 9. 探索性内容标准

探索性内容必须满足至少两个条件：

- 短期增长明显
- 技术路线新
- 与工程实践有潜在连接
- 来源可信
- 有 repo、demo、paper、benchmark、文档或真实案例可验证

排除纯营销、无实物概念、单平台孤立热度、标题党和明显刷热度内容。

## 10. 预算与资源约束

新增预算：0。

可用资源：

- 腾讯 Coding Plan
- 腾讯轻量云服务器：2 核 8G 内存，80G 存储
- 免费公开 RSS/API/网页
- 飞书群机器人 webhook
- 可选免费/本地/现有 LLM 能力

不依赖付费 X API、付费微信数据源、付费 RSS SaaS 或企业舆情系统。

## 11. 技术方案

第一版建议：

- Python 单体服务
- SQLite
- cron 定时任务
- 飞书 webhook 推送
- Markdown 文件人工审核
- 可插拔 LLM provider

目录形态示例：

```text
sources.yaml
data/app.db
candidates/YYYY-MM-DD.json
candidates/YYYY-MM-DD.md
briefs/YYYY-MM-DD.md
logs/YYYY-MM-DD.log
```

每日流程：

1. 定时采集公开 RSS、GitHub、arXiv、网页、RSSHub、白名单链接。
2. 正文抽取、标准化、去重。
3. 规则评分，生成候选池。
4. 17:50 生成候选 Markdown / JSON。
5. 用户可在服务器上手动编辑最终 Markdown。
6. 18:10 自动读取最终简报并推送飞书。
7. 保存候选、入选、运行日志和错误信息。

无 LLM 时，系统也必须可运行：用标题、正文前几段、关键词、来源权重、GitHub 指标生成基础摘要和评分。

有 LLM 时，只对 Top 20-30 候选做摘要、关键变化、为什么重要、可落地启发生成。

## 12. 数据模型草案

核心字段：

- id
- title
- source_name
- source_type
- url
- canonical_url
- published_at
- collected_at
- language
- raw_text / extracted_text
- summary
- key_changes
- why_matters
- practical_takeaway
- tags
- score
- score_reasons
- dedupe_key
- selected_for_brief
- brief_date
- created_at
- updated_at

## 13. 失败兜底

- 单个源失败不影响整体任务。
- 飞书推送失败要重试并写日志。
- 候选少于 10 条时少发，不硬凑。
- 候选总数低于 5 条或 P0 源大面积失败时，发送健康告警。
- 每次运行记录采集数量、失败源、入选数量、推送状态。

## 14. MVP 验收标准

- 连续 7 天每天 18:10 成功生成并推送飞书简报。
- 每天 10-15 条，最多 20 条。
- Top 3 至少 2 条被用户认为值得读。
- 每天至少 3 条 AI coding / Agentic Coding / 软件交付工程实践相关内容；若当天确实没有高质量内容，可以少于 3 条。
- 每天 1-2 条探索性高信号内容。
- 重复率低于 10%。
- 人工审核不超过 10 分钟。
- 每条都有来源链接和时间信息。
- 候选和入选内容都可归档查询。
- 无 LLM 时仍可生成基础简报。

## 15. 后续迭代

第一阶段：跑通 RSS/GitHub/arXiv/HN/部分博客/飞书推送。

第二阶段：扩充源清单、加 RSSHub、加强 GitHub 趋势和去重。

第三阶段：接入可用 LLM，提升摘要质量。

第四阶段：做简单 FastAPI 审核页面。

第五阶段：加入反馈机制，用“有用/无用/重复/低价值”优化评分。
