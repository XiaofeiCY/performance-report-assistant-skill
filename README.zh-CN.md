# Performance Report Assistant Skill

[English](README.md) | [简体中文](README.zh-CN.md)

一个开源的 Claude Code / Codex skill，仓库名为 `performance-report-assistant-skill`，用来把周报、git commit、工作记录和 Excel 模板整理成可提交的绩效汇报、工作总结或进度同步材料。

旧仓库名为 `anche-report-skill`。

这个 skill 面向所有需要定期写工作汇报的人，尤其适合最终输出必须填写到固定公司 Excel 模板里的场景。

## 能帮你做什么

- 周报总结
- 月度绩效自评
- 季度业务或项目复盘
- 晋升 / 述职材料
- 面向直属领导、管理层或总部的汇报
- 面向客户、甲方或非专业对象的进度同步
- 保留原始 Excel 模板样式的绩效表填写

## 为什么需要它

很多工作汇报并不是从零开始写，而是从一堆分散材料里整理出来：

- 周报
- 项目记录
- 工单
- 会议纪要
- git commit
- 产品或工程里程碑
- 客户反馈
- 固定 Excel 表单

普通 AI 生成 Excel 时很容易丢失原始模板样式，导致用户最后还要手动把内容复制回公司文件。这个 skill 采用更稳妥的流程：

1. 一步一步采访用户。
2. 先读取 Excel 模板。
3. 明确说明会修改哪些工作表、单元格或区域。
4. 等用户确认后再执行。
5. 写入原始模板的副本，而不是覆盖原文件。
6. 最后返回生成文件的保存路径。

## 核心特性

- 面向新用户的采访式引导
- 根据汇报对象调整表达方式
- 从周报和 git commit 中提取证据
- 使用 `openpyxl` 尽量保留 Excel 模板结构和样式
- 修改 Excel 前必须先确认改动范围
- 默认支持中文职场汇报
- 提供可复用脚本，用于收集 commit 和填写 Excel

## 仓库结构

```text
performance-report-assistant/
  SKILL.md
  agents/
    openai.yaml
  references/
    intake-questions.md
    report-patterns.md
    template-workflow.md
    excel-template-workflow.md
  scripts/
    collect_git_commits.py
    fill_excel_template.py
    resolve_report_period.py
```

## 安装方式

把 `performance-report-assistant` 文件夹复制到本地 skills 目录。

如果你的 Claude Code / Codex 环境使用 `.agents\skills`：

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<你的用户名>\.agents\skills" -Recurse -Force
```

如果你的环境使用 `.codex\skills`，可以复制到：

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<你的用户名>\.codex\skills" -Recurse -Force
```

安装后建议重启 Claude Code / Codex，或者新开一个会话。

## 使用方式

安装后可以这样说：

```text
使用 $performance-report-assistant，一步一步采访我，帮我完成一份月度绩效汇报。
```

也可以不安装，直接通过路径使用：

```text
请使用 E:\path\to\performance-report-assistant 这个 skill，一步一步引导我完成工作汇报。
```

## 推荐流程

1. 选择材料类型：周报总结、月度绩效、季度复盘、述职材料、领导汇报或客户同步。
2. 选择汇报对象：直属领导、管理层、跨部门伙伴、客户或非专业读者。
3. 提供汇报周期。
4. 如果有 Excel 模板，先提供模板。
5. 让 agent 先读取模板，并提出明确的改动计划。
6. 确认改动计划。
7. 提供周报、工作记录、工单摘要或 git 仓库路径等证据。
8. 生成汇报内容，并填写到模板副本中。
9. 检查最终返回的文件保存路径。

## Excel 模板安全策略

当用户提供 Excel 模板时，skill 会要求 agent：

- 先读取模板，不直接修改。
- 列出计划修改的工作表、单元格或区域。
- 避开公式、评分栏、审批栏、签名区、表头、样式、边框和合并单元格结构。
- 等用户明确确认后再执行。
- 写入模板副本，不覆盖原始文件。

## 脚本说明

### `collect_git_commits.py`

从一个或多个 git 仓库按时间范围提取 commit，输出 Markdown 证据材料。

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --since 2026-05-01 --until 2026-06-01 --output commits.md
```

### `fill_excel_template.py`

根据 JSON 映射把内容写入 Excel 模板副本，并尽量保留工作簿结构和样式。

```bash
python scripts/fill_excel_template.py --template template.xlsx --mapping mapping.json --output filled.xlsx
```

映射示例：

```json
{
  "绩效自评!C6": "本月重点完成...",
  "绩效自评!C7": "下月计划..."
}
```

### `resolve_report_period.py`

将"本周"、"上周"、"本月"、"上个月/上月"等相对时间描述解析为绝对日期范围。周报默认使用周一至周五的工作周，除非明确要求自然周模式。

```bash
python scripts/resolve_report_period.py --period 上周 --today 2026-06-09
```

自然周示例：

```bash
python scripts/resolve_report_period.py --period 上周 --today 2026-06-09 --week-mode natural
```

## 搜索关键词

performance-report-assistant-skill、performance report assistant skill、performance report assistant、anche-report-skill、anche report skill、Performance Report Assistant、Claude Code skill、Codex skill、AI agent skill、绩效汇报助手、绩效报告助手、工作汇报助手、周报总结、Excel 模板填写、中文绩效自评、述职材料、git commit 工作总结、stakeholder update、workplace report automation。

## 当前限制

- 企业微信 / WeCom 周报不一定能自动读取，取决于授权、连接器、浏览器自动化能力或用户导出的文本。
- 复杂 Excel 模板仍然需要人工确认单元格映射。
- 当前版本重点是采访式流程和安全填写模板；更高级的自动模板扫描能力可以后续扩展。

## 后续优化方向

- 增加 Excel 模板扫描脚本，自动推荐候选填写区域。
- 增加常见绩效模板示例。
- 增加研发、产品、测试、运营、项目经理、销售等岗位写作模式。
- 增加个人或团队写作风格配置。
