# Intake Questions

Use these questions selectively. Ask only what is needed. Lead the user step by step instead of presenting the whole list at once.

## Interview Flow

Start with one question:

```text
我会一步一步带你完成。先确认这次要写哪类材料：周报总结、月度绩效自评、季度复盘、述职材料、领导汇报，还是客户进度同步？
```

Then ask the next question based on the answer. For new users, prefer this sequence:

1. Report type.
2. Audience.
3. Date range.
4. Whether a fixed template file exists, or whether the user only has a previous filled report as an example.
5. Evidence sources for the target date range.
6. Git author, if a repository is provided and the user wants only their own commits.
7. Emphasis and sensitive points.

Do not ask for template, weekly reports, git repos, and style preferences all in the first message.

For relative dates:

- Resolve "上周" as the previous Monday through Friday using the current date and timezone.
- Resolve "本周" as the current Monday through Friday unless the user asks for work completed so far.
- Do not start "本周" from today's date. It starts on Monday.
- Do not include Saturday or Sunday for weekly work reports unless the user explicitly asks for a natural week, weekend work, or gives dates that include weekends.
- Use `scripts/resolve_report_period.py` for date arithmetic instead of calculating by memory.
- After resolving a relative period, state the exact date range and continue. Do not keep asking for the date range unless the resolved range is ambiguous.

## Minimum Questions

1. 这次要写哪类材料：周报总结、月度绩效自评、季度复盘、晋升述职、领导汇报、客户进度同步？
2. 汇报对象是谁：直属领导、部门负责人/总部领导、跨部门伙伴、甲方/客户、还是多人混合？
3. 是否有固定模板文件？可以是 Excel、Word、PPT、Markdown 或其他格式。如果只是以前提交过的周报/绩效表，把它当作风格和结构参考，不要当作本次答案。
4. 目标周期是什么？例如 2026 年 5 月、某个自然周、某个季度。
5. 这段时间最重要的 1-3 件事是什么？

## Evidence Questions

- 有哪些周报、会议纪要、需求文档、工单、PR、git commit 可以作为依据？
- 如果提供了代码仓库：必须先确认分支范围后再做研发数据统计，用提交次数、涉及文件、代码增删行、高频文件、作者分布、日期分布等角度支撑报告。
- **分支范围确认**：用户提供仓库后，在运行任何统计脚本之前，必须让用户选择当前分支、指定分支还是全部分支。脚本本身保留”未传 branch 时默认全部分支”的兜底行为，但 agent 采访不能静默默认全部分支。
- 如果用户明确指定分支：只统计该分支。
- **作者确认**：对个人周报、个人绩效或”我的提交”场景，即使 agent 知道用户是谁，也必须确认 git author 名称或邮箱。提示：”如果只统计你的提交，请确认 git author 名称或邮箱。可以给一个或多个；如果你要统计全部作者，我会在报告里把它标为仓库整体证据，不写成全部都是你的个人提交。”
- 如果用户不提供 author：统计全部作者并标注为仓库整体证据，不得写成个人提交。
- 如果提供的是 GitHub/GitLab 等仓库 URL：我会用统计脚本克隆到临时目录，统计完成后自动删除临时 clone，不会长期保存在本地。
- 哪些工作是你主导，哪些是参与或协同？
- 有无可量化结果：节省时间、减少问题、交付数量、上线范围、反馈评分、客户/领导反馈？
- 如果没有指标，有无定性证据：关键节点按期完成、风险被提前暴露、流程被沉淀、问题被闭环？

## Positioning Questions

- 这次最希望领导看到你的哪种能力：执行力、技术深度、业务理解、项目推进、跨部门协作、风险意识、客户沟通？
- 哪些内容需要弱化：未完成事项、争议、过细技术细节、内部敏感信息？
- 是否需要体现下月计划、资源诉求、风险预警或改进动作？

## Template Questions

- 表格每一栏希望写多长：一句话、短段落、项目符号、还是详细说明？
- 模板是否有固定字段、章节、页面、幻灯片、表格、占位符或示例行？如果有，优先模仿它的结构、粒度和口吻。
- 如果用户粘贴的是以前提交过的周报或绩效内容，先确认：“我会把这份旧内容当作格式/口吻参考。请再提供本周期的实际工作内容或代码仓库证据。”
- 是否需要保留公式、合并单元格、颜色、边框、打印区域、审批栏、签名区、页面版式、幻灯片布局或图表？

## Guardrail Prompts

Use these when the conversation is about to go wrong:

```text
我会按工作周处理周报：默认周一到周五，不包含周末。按当前日期换算，这里的”上周”是 [YYYY-MM-DD] 到 [YYYY-MM-DD]；如果你要自然周或包含周末，请告诉我。
```

```text
我看到你提供的是以前提交过的周报，并且你说只参考结构/格式。我会只提取缩进、换行、中括号、分组方式、统计行形态等格式信号；不会复用里面的事项、仓库名、模块名、commit 数或统计数字。当前周期证据只以你接下来的仓库、周报、说明或其他材料为准。
```

```text
我看到你提供的是以前提交过的周报。我会把它当作格式和口吻参考，不会直接作为本周答案。请继续给我本周实际完成的事项、周报草稿、会议记录，或代码仓库路径。
```

```text
这份内容是本周期实际事项，还是只作为格式/结构参考？如果只是参考，我不会复用里面的事项、仓库名或统计数字。
```

```text
你提供了代码仓库。代码统计前我先确认扫描范围：这些仓库要看当前分支、指定分支，还是全部分支？如果选指定分支，请给分支名。
```

```text
如果只统计你的提交，请确认 git author 名称或邮箱。可以给一个或多个；如果你要统计全部作者，我会在报告里把它标为仓库整体证据，不写成全部都是你的个人提交。
```

```text
我会把这个仓库 URL 交给统计脚本处理。脚本会克隆到系统临时目录，统计完成后自动清理；不会把仓库长期留在当前项目里。
```

```text
现在还缺本周期证据。我可以继续采访你，也可以基于你提供的代码仓库先确认分支、作者等参数后统计提交次数、涉及文件、代码增删行和高频改动文件。
```

```text
你提供了固定模板。我会先识别它是 Excel、Word、PPT、Markdown 还是其他格式，再说明计划改动哪些字段/章节/页面/幻灯片；确认后才会写入副本。
```

```text
执行代码数据统计前，请你确认以下信息：
- 时间范围：[YYYY-MM-DD] 到 [YYYY-MM-DD]
- 仓库：[repo A]、[repo B]
- 分支范围：[当前分支 / 指定分支 xxx / 全部分支]
- 作者过滤：[author 名称/邮箱 / 不过滤全部作者]
- 统计口径：[仅个人提交 / 仓库整体证据]
- 旧周报用途：仅参考结构，不复用内容和仓库名

确认无误后我再执行统计。请明确回复”确认执行”或指出要调整的项。
```

```text
你之前提供的旧周报里出现了 [仓库X/模块Y]，但当前你只给了 [仓库A 和 仓库B]。我不会把旧周报里的仓库或模块当作当前缺失项来追问；如果你需要补充其他仓库或材料，请直接告诉我。
```

## Template Confirmation Prompt

After inspecting an uploaded template, confirm before writing:

```text
我已经读完模板。计划改动以下位置：
- [文件区域/字段/章节/页面/幻灯片]：[用途]

我不会改动：
- 公式单元格/图表/自动计算区域
- 评分/评级栏
- 审批/签名区域
- 表头、样式、边框、合并单元格、页面版式、幻灯片布局

请确认是否按这个方案继续？确认后我再生成填写后的文件副本。
```
