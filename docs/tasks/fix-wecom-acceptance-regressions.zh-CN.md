# 任务：修复企微安全边界验收未通过项

## 最新验收结论（Codex 第二轮验收后）

Claude 已按本任务做过一轮返工。Codex 第二轮验收结论：**仍未通过，但只剩两个小返工点**。

后续 Claude 只需要修复本节列出的两个问题，不要扩展企业微信自动化能力，不要跑企业微信实机自动化。

### 剩余返工 1：`click_new_summary_plus()` 仍允许 unknown page

当前问题：

- `_try_click_plus_loose()` 已经收紧，会拒绝 `smart_summary_unknown_page`。
- 但 `click_new_summary_plus()` 自己的 guard 仍允许 `smart_summary_unknown_page`。
- 虽然当前调用方通常先判断过历史页，但 `click_new_summary_plus()` 会在点击前重新截图/OCR 分类；如果即时分类结果变成 unknown，它现在仍可能继续 OCR 找 `+` 并点击。

要求：

- `click_new_summary_plus()` 只能接受 `smart_summary_history_result_page`。
- 如果点击 `+` 前即时分类结果是 `smart_summary_unknown_page`，必须保存截图/OCR 后安全失败。
- unknown page 不能走任何 `+` 恢复路径。
- 不要新增坐标 fallback，不要新增更多页面猜测。

### 剩余返工 2：`fill_excel_template.py` 预期拒绝路径仍有 traceback

当前问题：

- Excel 后缀矩阵的返回码已经正确。
- `.xlsm -> .xlsx`、`.xltx -> .xltx`、`.xltm -> .xltm`、`.xls` 输入/输出等预期拒绝路径会先打印 Python traceback，再显示中文错误。
- 这不符合“不支持格式有可读错误，不是堆栈崩溃”的验收标准。

要求：

- 对已知校验失败输出简洁中文错误，并以非 0 状态退出。
- 不要为预期拒绝路径打印 Python traceback。
- 至少覆盖：
  - `.xlsm -> .xlsx` 拒绝，无 traceback；
  - `.xltx -> .xltx` 拒绝，无 traceback；
  - `.xltm -> .xltm` 拒绝，无 traceback；
  - `.xls` 输入拒绝，无 traceback；
  - `.xls` 输出拒绝，无 traceback。
- 真正意外异常可以保留诊断，但已知格式/后缀校验失败不能像堆栈崩溃。

### 第二轮已通过项，不要重复大改

- `_try_click_plus_loose()` 已拒绝 `smart_summary_unknown_page`，并移除了 calibrated `+` 坐标。
- `copy_result()` 已接收 `wait_state` 并拒绝非本次生成状态。
- `copy_result()` 已拒绝 `smart_summary_unknown_page`、`smart_summary_input_page`、`main_or_unknown_page`。
- `wecom-smart-summary-collector.md` 已不再把“快捷键复制”列为允许行为。
- Excel 成功路径已通过：
  - `.xlsx -> .xlsx`
  - `.xlsm -> .xlsm` 且无 subprocess stderr
  - `.xltx -> .xlsx`
  - `.xltm -> .xlsm` 且无 subprocess stderr
- `.xltx -> .xltx`、`.xltm -> .xltm` 已能拒绝，只需要去掉 traceback。

### 第二轮后必须运行的验证

```powershell
python -m py_compile performance-report-assistant\scripts\collect_wecom_smart_summary.py performance-report-assistant\scripts\fill_excel_template.py
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
python performance-report-assistant\scripts\fill_excel_template.py --help
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py --manual-input --output outputs\wecom_summary_manual_test.md --output-json outputs\wecom_summary_manual_test.json
```

Excel 拒绝路径必须确认没有 traceback：

- `.xlsm -> .xlsx`
- `.xltx -> .xltx`
- `.xltm -> .xltm`
- `.xls` 输入
- `.xls` 输出

企业微信实机自动化仍然不要运行，必须等待用户监督。

## 背景

Claude 已执行 `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`，Codex 随后按该任务文档进行验收。

验收结论：暂不通过。整体方向已覆盖大部分需求，但仍存在几处和当前任务硬边界冲突的问题，尤其是“历史结果页不能复制为本次结果”和“未知页不能继续坐标试探”。

本任务只做返工修正，不扩展企业微信自动化能力。

## 用户当前要求

将 Codex 验收意见写入项目文档，作为后续交给 Claude 返工的明确任务。

## 目标

修复 Codex 验收发现的未通过项，使企业微信采集器和 Excel 后缀策略重新满足当前安全边界。

## 必须修复

### 1. 复制阶段不得复制历史结果页

当前问题：

- `copy_result()` 在复制前允许 `smart_summary_history_result_page` 继续进入滚动和 OCR 点击“复制”。
- 历史结果页也可能显示“复制”按钮，但它不是本次智能总结结果。

要求：

- 历史结果页只能用于点击 `+` 新建本次总结。
- 复制前必须确认页面是“本次提交后产生的结果页 / 复制可用页”。
- 不允许仅因为页面存在“复制”按钮就复制。
- 至少需要在状态机中区分：
  - `smart_summary_history_result_page`
  - `smart_summary_input_page`
  - `smart_summary_current_result_page` 或等价的“本次结果可复制”状态
- 如果无法确认是本次结果页，应停止并保存截图/OCR，提示用户手动复制或使用 `--manual-input`。

### 2. 未知智能总结页不得继续 loose 坐标点击

当前问题：

- `_try_click_plus_loose()` 接受 `smart_summary_unknown_page`，并使用多个校准坐标尝试点击 `+`。
- 这和 unknown page 应保存诊断并有界失败的边界不一致。

要求：

- `smart_summary_unknown_page` 应保存截图/OCR 后安全失败，或只在能重新分类为历史结果页 / 输入页后继续。
- 移除 `_try_click_plus_loose()` 对未知页的多固定坐标试探。
- 如果保留 `+` 点击，只允许在确认 `smart_summary_history_result_page` 后执行。
- `+` 点击必须仍然有界、可诊断；失败后停止，不回退到更多猜测。

### 3. 修正文档中的“快捷键复制”边界

当前问题：

- `performance-report-assistant/references/wecom-smart-summary-collector.md` 仍把“快捷键复制”列为允许行为。
- 这容易和禁止未知区域 `Ctrl+A/Ctrl+C` 的安全边界冲突。

要求：

- 不要把“快捷键复制”列为允许行为。
- 改为：只允许点击已验证的“复制”按钮。
- 明确禁止对未知区域使用快捷键复制、`Ctrl+A/Ctrl+C` 或右键菜单复制。
- 确保以下文档说法一致：
  - `README.md`
  - `README.zh-CN.md`
  - `performance-report-assistant/SKILL.md`
  - `performance-report-assistant/references/intake-questions.md`
  - `performance-report-assistant/references/wecom-smart-summary-collector.md`

### 4. 修复 Excel 后缀策略和宏路径验证噪音

当前问题：

- `.xltm` 当前允许输出 `.xltm`，但任务要求模板输出为 `.xlsm`。
- `.xltx` 当前允许输出 `.xltx`，但任务要求模板输出为 `.xlsx`。
- Codex 最小验证中 `.xlsm` / `.xltm` 路径虽然返回码为 0 且单元格写入成功，但 stderr 出现：

```text
ValueError: I/O operation on closed file.
```

要求：

- `.xltm` 模板只能输出 `.xlsm`，不得允许 `.xltm` 输出。
- `.xltx` 模板只能输出 `.xlsx`，不得允许 `.xltx` 输出。
- `.xlsm` / `.xltm` 路径运行时不能在 stderr 出现 `ValueError: I/O operation on closed file`。
- 如果无法保证宏保留，应明确拒绝并给出可读错误，不要假装支持。

## 建议执行步骤

1. 修改企业微信页面分类和等待/复制状态，增加“本次结果页 / 复制可用页”的明确判断。
2. 收紧 `copy_result()` 的入口条件，不接受历史结果页或未知页。
3. 删除或收紧 `_try_click_plus_loose()`，禁止未知页多坐标点击。
4. 修正企微参考文档中的“快捷键复制”措辞。
5. 修正 Excel 后缀校验逻辑。
6. 运行最小验证并记录结果。

## 必须运行的验证

```powershell
python -m py_compile performance-report-assistant\scripts\collect_wecom_smart_summary.py performance-report-assistant\scripts\fill_excel_template.py
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
python performance-report-assistant\scripts\fill_excel_template.py --help
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py --manual-input --output outputs\wecom_summary_manual_test.md --output-json outputs\wecom_summary_manual_test.json
```

Excel 最小验证：

- `.xlsx -> .xlsx` 成功。
- `.xlsm -> .xlsm` 成功且无 stderr 异常，或清晰拒绝。
- `.xlsm -> .xlsx` 拒绝。
- `.xltx -> .xlsx` 成功。
- `.xltx -> .xltx` 拒绝。
- `.xltm -> .xlsm` 成功且无 stderr 异常，或清晰拒绝。
- `.xltm -> .xltm` 拒绝。
- `.xls` 输入 / 输出拒绝且错误可读。

## 不要做

- 不要扩展新的企业微信自动化能力。
- 不要恢复 `CLAUDE.md` / `AGENT.md`。
- 不要读取 `docs/archive/tasks/` 作为当前执行指令。
- 不要把历史结果页复制为本次结果。
- 不要在未知页继续坐标试探。
- 不要用右键菜单、未知区域快捷键复制或 `Ctrl+A/Ctrl+C` 作为默认 fallback。

## 验收标准

- `copy_result()` 不再接受历史结果页或未知页作为可复制结果页。
- 历史结果页只用于 `+` 新建本次总结。
- 未知页安全失败并保存诊断，不做 loose 坐标点击。
- 文档中不再把“快捷键复制”描述为允许行为。
- Excel 后缀策略与任务要求一致。
- `.xlsm` / `.xltm` 处理路径没有 stderr 异常；如不支持则清晰拒绝。
- 所有必须运行的验证通过，企业微信实机测试仍等待用户监督执行。

## 备注

企业微信实机自动化测试必须由用户在本机监督下执行。Claude 不要擅自运行实机自动化。
