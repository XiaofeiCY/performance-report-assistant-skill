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

普通 AI 生成 Excel 时很容易丢失原始模板样式，导致用户最后还要手动把内容复制回公司文件。这个 skill 采用先预览、后决定是否导出的流程：

1. 一步一步采访用户。
2. 旧报告和模板默认只参考结构与表达，不作为本周期事实。
3. 完整展示证据来源，包括手工材料、文件、git 和用户监督下的企微采集。
4. 先在对话中生成完整内容并修改。
5. 只有用户明确要求保存时，才确认格式和输出位置。
6. 导出到固定模板时写入副本，不覆盖原文件。

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
    git-evidence-rules.md
    report-patterns.md
    template-workflow.md
    excel-template-workflow.md
    wecom-smart-summary-collector.md
  scripts/
    collect_git_commits.py
    collect_wecom_smart_summary.py
    fill_excel_template.py
    resolve_report_period.py
    requirements-wecom.txt
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
4. 提供空白模板、仅供格式参考的旧报告，或选择无模板；旧模板内容不会自动进入新报告。
5. 多选本次证据来源：直接描述、粘贴文本、文件、git 仓库、用户监督下的企微智能总结，或暂无补充材料。
6. 先在对话中查看并修改完整预览。
7. 如需持久文件，再明确提出导出并确认绝对输出路径。
8. 固定模板导出前确认具体填写位置，并写入原模板副本。

## Excel 模板安全策略

当用户提供 Excel 模板时，skill 会要求 agent：

- 先读取模板，不直接修改。
- 列出计划修改的工作表、单元格或区域。
- 避开公式、评分栏、审批栏、签名区、表头、样式、边框和合并单元格结构。
- 等用户明确确认后再执行。
- 写入模板副本，不覆盖原始文件。

## 脚本说明

### `collect_git_commits.py`

从一个或多个 git 仓库按时间范围提取 commit。默认不传 `--output`，直接把证据打印到 stdout 供预览。

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --since 2026-05-01 --until 2026-06-01
```

只有用户明确要求保存证据文件时，才增加 `--output <绝对路径>`。

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
- 企业微信智能总结桌面自动化（`collect_wecom_smart_summary.py`）**仅限 Windows**，必须由用户**在本机监督下执行**，**不是稳定的无人值守或跨平台能力**。采集器无法适配所有企业微信 UI 变体；无法验证目标页面、生成状态或复制按钮时会安全停止并保存诊断。自动化失败时可改用 `--manual-input` 手动输入。
- 企微采集器不会：沿左侧菜单纵向扫描、右键菜单复制、坐标猜测复制按钮、对未知区域 Ctrl+A/Ctrl+C。入口定位仅限于 UIA/OCR 精确匹配和单个不稳定 probe 坐标。
- 复杂 Excel 模板仍然需要人工确认单元格映射。
- Excel 填充支持 `.xlsx`、`.xlsm`（保留宏）、`.xltx`/`.xltm`（模板转工作簿），不支持 `.xls`（需先在 Excel 中另存）。
- 当前版本重点是采访式流程和安全填写模板；更高级的自动模板扫描能力可以后续扩展。

## 后续优化方向

- 增加 Excel 模板扫描脚本，自动推荐候选填写区域。
- 增加常见绩效模板示例。
- 增加研发、产品、测试、运营、项目经理、销售等岗位写作模式。
- 增加个人或团队写作风格配置。
