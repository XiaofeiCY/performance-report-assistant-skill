# Performance Report Assistant

一个面向中文职场汇报的 Codex / Claude Code skill，用来把周报、git commit、项目材料和公司 Excel 模板整理成可提交的工作汇报。

它特别适合这些场景：

- 周报总结
- 月度绩效自评
- 季度复盘
- 晋升 / 述职材料
- 直属领导或总部领导汇报
- 面向甲方、客户、非专业对象的进度同步
- 保留公司原始 Excel 模板样式的绩效表填写

## 为什么做这个 skill

很多公司的绩效汇报不是写一篇文章，而是填写固定 Excel 表。不同部门模板不同，用户往往需要先从企业微信等地方整理周报，再手动复制到 AI 生成结果里，最后还要把内容重新粘回原始 Excel 模板。

这个 skill 的目标是降低这部分操作成本：

- 用采访式流程一步步引导用户，而不是一上来要求准备所有材料。
- 先读取 Excel 模板，列出计划修改的位置，等用户确认后再写入。
- 尽量保留原始 Excel 的样式、合并单元格、公式、边框和表结构。
- 支持从 git commit 中提取工作证据。
- 根据不同汇报对象调整表达方式。

## 目录结构

```text
performance-report-assistant/
  SKILL.md
  agents/
    openai.yaml
  references/
    intake-questions.md
    report-patterns.md
    excel-template-workflow.md
  scripts/
    collect_git_commits.py
    fill_excel_template.py
```

## 安装方式

把 `performance-report-assistant` 文件夹复制到你的 skills 目录。

Claude Code / Codex 常见目录示例：

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<你的用户名>\.agents\skills" -Recurse -Force
```

如果你的环境使用 `.codex\skills`，也可以复制到：

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<你的用户名>\.codex\skills" -Recurse -Force
```

复制后建议重启 Claude Code / Codex，或新开一个会话。

## 使用方式

安装后可以这样说：

```text
使用 $performance-report-assistant，一步一步采访我，帮我完成 5 月月度绩效汇报。
```

如果你还没有安装，也可以直接按路径使用：

```text
请使用 E:\work\anche_report_skill\performance-report-assistant 这个 skill，一步一步采访我，帮我完成月度绩效汇报。
```

## 推荐工作流

1. 说明要写的材料类型，例如月度绩效、周报总结、季度复盘。
2. 说明汇报对象，例如直属领导、总部领导、客户。
3. 提供汇报周期。
4. 如果有 Excel 模板，先提供模板。
5. skill 会先读取模板，并告诉你计划修改哪些工作表、单元格或区域。
6. 你确认后，再提供周报、git 仓库路径或其他证据材料。
7. skill 生成汇报内容，并写入模板副本。
8. 最后返回生成文件的保存路径。

## Excel 模板安全策略

当你提供 Excel 模板时，skill 应该：

- 先读模板，不直接修改。
- 列出计划改动的单元格或区域。
- 说明不会改动公式、评分栏、审批栏、签名区、样式、边框、合并单元格。
- 等你明确确认后，再生成填写后的文件。
- 默认写入模板副本，不覆盖原始模板。

## 脚本说明

### `collect_git_commits.py`

按时间范围从一个或多个 git 仓库提取 commit，生成 Markdown 证据材料。

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --since 2026-05-01 --until 2026-06-01 --output commits.md
```

### `fill_excel_template.py`

根据 JSON 映射把内容写入 Excel 模板副本，尽量保留原始样式。

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

## 发布前建议

如果你要把它发布到 GitHub，建议仓库根目录增加 `.gitignore`：

```gitignore
.claude/
__pycache__/
*.pyc
work/
*.tmp
```

## 当前限制

- 企业微信周报无法保证自动读取，取决于你的授权、连接器或浏览器自动化能力。
- Excel 模板识别依赖 agent 对表结构的理解。复杂模板建议先让 agent 列出拟修改单元格，并人工确认。
- 如果需要更强的自动映射能力，可以后续增加模板扫描脚本。

## 适合继续优化的方向

- 自动扫描 Excel 模板并生成候选填充区域。
- 增加真实公司模板样例测试。
- 增加不同岗位的默认表达风格，例如研发、测试、产品、项目经理、运营。
- 增加个人写作风格配置文件。
