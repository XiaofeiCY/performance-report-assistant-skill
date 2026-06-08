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
4. Whether a fixed Excel template exists, or whether the user only has a previous filled report as an example.
5. Evidence sources for the target date range.
6. Repository branch, if a repository is provided and the user has not named a branch.
7. Emphasis and sensitive points.

Do not ask for template, weekly reports, git repos, and style preferences all in the first message.

For relative dates:

- Resolve "上周" as the previous Monday through Sunday using the current date and timezone.
- Resolve "本周" as the current Monday through Sunday unless the user asks for work completed so far.
- After resolving a relative period, state the exact date range and continue. Do not keep asking for the date range unless the resolved range is ambiguous.

## Minimum Questions

1. 这次要写哪类材料：周报总结、月度绩效自评、季度复盘、晋升述职、领导汇报、客户进度同步？
2. 汇报对象是谁：直属领导、部门负责人/总部领导、跨部门伙伴、甲方/客户、还是多人混合？
3. 是否有固定格式或 Excel 模板？如果只是以前提交过的周报/绩效表，把它当作风格和结构参考，不要当作本次答案。
4. 目标周期是什么？例如 2026 年 5 月、某个自然周、某个季度。
5. 这段时间最重要的 1-3 件事是什么？

## Evidence Questions

- 有哪些周报、会议纪要、需求文档、工单、PR、git commit 可以作为依据？
- 如果提供了代码仓库：这次统计看哪个分支？如果没有指定，我会按仓库默认分支统计。
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
- 表格是否已有示例行或往月填法？如果有，优先模仿它的粒度和口吻。
- 如果用户粘贴的是以前提交过的周报或绩效内容，先确认：“我会把这份旧内容当作格式/口吻参考。请再提供本周期的实际工作内容或代码仓库证据。”
- 是否需要保留公式、合并单元格、颜色、边框、打印区域或审批栏？

## Guardrail Prompts

Use these when the conversation is about to go wrong:

```text
我看到你提供的是以前提交过的周报。我会把它当作格式和口吻参考，不会直接作为本周答案。请继续给我本周实际完成的事项、周报草稿、会议记录，或代码仓库路径。
```

```text
你提供了代码仓库。为了避免统计错分支，请先确认这次看哪个分支？如果没有特别要求，我会按仓库默认分支统计。
```

```text
我会把这个仓库 URL 交给统计脚本处理。脚本会克隆到系统临时目录，统计完成后自动清理；不会把仓库长期留在当前项目里。
```

```text
现在还缺本周期证据。我可以继续采访你，也可以基于你提供的代码仓库先统计提交次数、涉及文件、代码增删行和高频改动文件。
```

## Template Confirmation Prompt

After inspecting an uploaded Excel template, confirm before writing:

```text
我已经读完模板。计划改动以下位置：
- [工作表]![单元格]：[用途]

我不会改动：
- 公式单元格
- 评分/评级栏
- 审批/签名区域
- 表头、样式、边框、合并单元格

请确认是否按这个方案继续？确认后我再生成填写后的 Excel。
```
