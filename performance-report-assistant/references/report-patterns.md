# Report Patterns

Use these default structures only when the user has no fixed template.

## Weekly Summary

If the user provides a previous weekly report, use it only to mirror section order, tone, and granularity. Replace all content with current-week evidence.

```markdown
## 本周完成
- [事项]：[结果]。[必要时补充影响或范围]

## 本周重点推进
- [事项]：[进展]。[卡点/协作对象/下一步]

## 研发证据摘要（有仓库时使用）
- [分支]：[提交次数/涉及文件数/代码增删行/高频模块]。[说明它支撑的交付或问题闭环]

## 问题与风险
- [问题]：[影响]。[处理动作或需要支持]

## 下周计划
- [计划]：[目标结果]
```

## Monthly Performance Self-Review

```markdown
## 本月重点工作
1. [主题一]
   - 完成内容：
   - 个人角色：
   - 结果与影响：
   - 证据来源：

2. [主题二]
   - 完成内容：
   - 个人角色：
   - 结果与影响：
   - 证据来源：

## 研发证据摘要（有仓库时使用）
- 提交次数：
- 涉及文件数：
- 代码改动行数：
- 当前代码规模：
- 高频改动文件：

## 能力体现
- 执行交付：
- 问题解决：
- 协同推进：
- 业务理解/客户意识：

## 问题与改进
- [不足或风险]：[改进动作]

## 下月计划
- [目标]：[关键动作]：[预期结果]
```

## Leadership / Headquarters Update

```markdown
## 核心结论
[用 1-2 句话说明周期内最重要的结果、风险或决策诉求]

## 关键进展
- [结果]：[业务/组织影响]

## 研发证据摘要（有仓库时使用）
- [周期内代码证据]：[提交次数/涉及文件数/代码增删行/高频模块]。[用一句话解释它支撑了什么业务或工程结果]

## 风险与应对
- [风险]：[影响]：[当前应对]：[需要支持]

## 下阶段计划
- [里程碑]：[时间]：[预期结果]
```

## Customer / Non-Expert Progress Update

```markdown
## 当前进展
- [客户能理解的成果]：[带来的好处]

## 已解决问题
- [问题]：[解决方式]：[当前状态]

## 接下来安排
- [事项]：[预计时间]：[客户需要配合的内容]

## 需确认事项
- [问题]：[建议选项或需要的反馈]
```

## Promotion / Role Expansion Review

```markdown
## 关键贡献
- [高影响事项]：[本人职责]：[结果]：[组织价值]

## 研发证据摘要（有仓库时使用）
- [分支]：[提交次数/涉及文件数/代码增删行/高频模块]。[说明它体现的职责范围、技术深度或交付稳定性]

## 能力成长
- [能力维度]：[具体证据]：[可复用经验]

## 影响范围
- 对项目：
- 对团队：
- 对客户/业务：

## 后续规划
- [更高一级职责的承接方式]
```

## Writing Heuristics

- Start each section with outcome, then evidence, then role.
- Convert tasks into value: "完成接口联调" can become "打通 XX 流程的数据链路，支撑后续 XX 场景上线".
- Keep ownership accurate:
  - 主导: user drove planning, coordination, or final delivery.
  - 负责: user owned a defined module or deliverable.
  - 参与: user contributed but did not own the whole result.
  - 协同: user supported cross-team alignment or execution.
- Avoid empty adjectives such as "认真负责" unless followed by concrete evidence.
