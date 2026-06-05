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
4. Whether a fixed template exists.
5. Evidence sources.
6. Repository branch, if a repository is provided and the user has not named a branch.
7. Emphasis and sensitive points.

Do not ask for template, weekly reports, git repos, and style preferences all in the first message.

## Minimum Questions

1. 这次要写哪类材料：周报总结、月度绩效自评、季度复盘、晋升述职、领导汇报、客户进度同步？
2. 汇报对象是谁：直属领导、部门负责人/总部领导、跨部门伙伴、甲方/客户、还是多人混合？
3. 是否有固定格式或 Excel 模板？有的话先让用户提供模板；没有的话使用默认格式。
4. 目标周期是什么？例如 2026 年 5 月、某个自然周、某个季度。
5. 这段时间最重要的 1-3 件事是什么？

## Evidence Questions

- 有哪些周报、会议纪要、需求文档、工单、PR、git commit 可以作为依据？
- 如果提供了代码仓库：这次统计看哪个分支？如果没有指定，我会按仓库默认分支统计。
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
- 是否需要保留公式、合并单元格、颜色、边框、打印区域或审批栏？

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
