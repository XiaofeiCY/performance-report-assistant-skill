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

## WeCom Smart Summary Questions

仅在用户明确要求采集企微智能总结时使用。不要自动触发。

- 需要采集什么内容？例如：本周工作事项、临时生产修数、跨部门协调、风险跟进等。
- 我会根据已确认的报告周期生成默认采集提示词，你可以直接确认、修改或提供自己的提示词。
- 如果报告周期已经解析为具体日期，默认采集提示词必须让周期标签和用户原话保持一致。用户说"上周"时，只能写"上周（YYYY-MM-DD 至 YYYY-MM-DD）"或直接写"YYYY-MM-DD 至 YYYY-MM-DD 期间"。周期标签不明时用"目标周期内"，不要把当前周标签和上一周日期范围混在一起。
- 企微智能总结可能打开在三种状态：企微主聊天页、智能总结新建输入页、或上一次历史结果页。历史结果页不是本次证据，脚本应点击 `+` 新建本次总结后再输入提示词。
- 企业微信窗口可任意伸缩，脚本不得使用左侧菜单纵向扫描或多点试探来找入口；找不到可验证入口时应停止并保存诊断。
- 智能总结生成时间不固定，脚本会用结果页状态、文本稳定、结果操作区或复制按钮等可观察信号判断进度，固定超时只作为硬上限。
- 如果结果过长或窗口未完整显示，复制按钮可能在底部不可见；脚本只能在确认结果页后有限滚动查找复制按钮，找不到时应改用手动复制/`--manual-input`，不得右键乱试或对未知区域 Ctrl+A/Ctrl+C。
- 执行企微自动化前，必须确认以下前提条件（逐项展示，等待明确肯定）：
  - 已登录企业微信 Windows 客户端；
  - 已打开目标聊天/群/范围所在界面；如果已在智能总结历史结果页，也可以继续，但脚本需要先点击 `+` 新建本次总结；
  - 用户正在电脑前监督；
  - 允许脚本使用截图、OCR、Interception 输入和剪贴板读取；
  - 脚本不会发送、删除、编辑或转发任何消息；
  - 当前企微自动化仍处于本机验证/不稳定状态，只支持已验证的企微主界面、智能总结输入页、历史结果页新建恢复路径，以及结果页内受限复制路径；
  - 如果入口、生成状态或复制按钮无法验证，脚本会停止并保存诊断，不会继续乱点；
  - 如果自动化失败，可以改用手动粘贴智能总结结果。
- 未收到用户明确确认（如"确认执行企微采集"）前，不得执行企微自动化。
- 企微采集结果标记为 `needs_user_confirmation`，生成报告前提醒用户确认。

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

```text
你提到要采集企微智能总结。根据已确认的报告周期 [YYYY-MM-DD 到 YYYY-MM-DD]，我建议使用以下提示词：

[动态生成的默认 prompt。若用户原话是"上周"，写"总结上周（YYYY-MM-DD 至 YYYY-MM-DD）期间..."或"总结 YYYY-MM-DD 至 YYYY-MM-DD 期间..."；不要把当前周标签和上一周日期范围混在一起。]

你可以直接确认、修改提示词，或提供自己的提示词文件。
```

```text
执行企微智能总结采集前，请确认：
- 你已登录企业微信 Windows 客户端；
- 已打开目标聊天/群/范围所在界面；如果当前已在智能总结历史结果页，脚本会先点击 `+` 新建本次总结；
- 你正在电脑前监督；
- 允许脚本使用截图、OCR、Interception 输入和剪贴板读取；
- 脚本不会发送、删除、编辑或转发任何消息；
- 当前企微自动化仍处于本机验证/不稳定状态，只支持已验证的企微主界面、智能总结输入页和历史结果页新建恢复路径；
- 脚本不会沿企微左侧菜单纵向扫描，也不会在未知区域右键复制或 Ctrl+A/Ctrl+C；
- 如果自动化失败，可以改用手动粘贴智能总结结果；
- 输出路径为：[path]。

确认无误后我再执行。请明确回复"确认执行企微采集"。
```

```text
企微采集进度：正在检查运行环境和依赖。
企微采集进度：正在定位企业微信窗口。
企微采集进度：正在识别智能总结界面。
企微采集进度：检测到历史结果页，正在点击 + 新建本次总结。
企微采集进度：正在粘贴采集提示词。
企微采集进度：已点击开始总结，正在等待结果生成。
企微采集进度：检测到复制按钮，正在读取剪贴板。
企微采集完成：结果已保存到 [path]。
```

```text
企微采集失败：[具体原因]。
我已停止自动化操作，不会继续乱点。你可以调整窗口后重试，改用手动输入模式（--manual-input），或粘贴智能总结内容。
```

```text
企微智能总结是聊天记录摘要，可能遗漏或误解上下文。我会把它作为待确认证据使用，不会直接把讨论、计划或风险提醒写成已完成工作。
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
