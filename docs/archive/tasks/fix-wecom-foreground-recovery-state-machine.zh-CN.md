# 任务：修复企业微信前台恢复与智能总结入口状态机

## 背景

用户再次测试 `performance-report-assistant/scripts/collect_wecom_smart_summary.py` 后发现，脚本仍然容易在可恢复状态下停止。

当前失败现象：

- 脚本可以截图到企业微信聊天主页面。
- OCR 识别结果显示当前是企业微信主窗口/聊天列表/聊天内容，而不是智能总结输入页。
- 脚本检测到疑似“智能总结”子窗口后，因为页面验证不通过而停止。
- 用户期望脚本在这种情况下继续尝试把企业微信调到前台、扫描入口、进入智能总结，而不是遇到一个页面状态不符就退出。

用户最新明确要求：

> 前台不是企微，尝试调用出来，尝试几次后调不出来再停掉。

## 目标

把企业微信采集器的窗口状态处理改成可恢复状态机：

1. 当前前台不是企业微信时，不要立即失败。
2. 先尝试恢复、置前、聚焦企业微信窗口。
3. 多种恢复策略按顺序尝试，并有限重试。
4. 只有多次确认仍无法把企业微信置为前台时，才停止。
5. 当前前台已经是企业微信但页面不是智能总结页时，不应停止；应继续扫描并尝试进入智能总结入口。
6. 只有在粘贴 prompt、点击开始总结、复制结果等危险动作前，才必须要求“企业微信在前台 + 智能总结输入页验证通过”。

## 范围

建议修改：

- `performance-report-assistant/scripts/collect_wecom_smart_summary.py`
- `performance-report-assistant/references/wecom-smart-summary-collector.md`
- 如主 skill 的执行说明仍有误导，可同步更新 `performance-report-assistant/SKILL.md`
- 如访谈/确认文案仍要求用户手动进入智能总结页，可同步更新 `performance-report-assistant/references/intake-questions.md`

不要修改：

- Git 仓库统计逻辑。
- Excel 模板填充逻辑。
- 报告生成规则。
- 旧周报仅作结构参考的规则。

## 必须实现的行为

### 1. 前台不是企业微信时先恢复，不要立刻停

新增或重构窗口恢复函数，例如：

```text
ensure_wecom_foreground(max_attempts=3)
```

推荐每轮尝试包含：

- 枚举 `WeWorkWindow` 主窗口。
- 如果窗口最小化，先 `ShowWindow(..., SW_RESTORE)`。
- 调用 `ShowWindow` / `SetForegroundWindow` / `BringWindowToTop`。
- 必要时使用 `AttachThreadInput` 之类的前台恢复 fallback。
- 必要时做短暂 topmost nudge。
- 必要时点击已确认属于企业微信窗口的标题栏或可见区域，但不能大范围随机点击。
- 每次尝试后用 `GetForegroundWindow()`、root/owner/process/class/title 验证当前前台是否属于企业微信。

只有所有尝试失败后，才输出失败：

```text
企微采集失败：[stage] 多次尝试后仍无法将企业微信置于前台，已停止以避免误操作其他窗口。
```

### 2. 区分危险状态和可恢复状态

必须区分：

- 危险状态：找不到企业微信窗口，或多次恢复后前台仍不是企业微信。
- 可恢复状态：前台是企业微信，但当前仍在聊天主界面、联系人列表、群列表或聊天内容页。

危险状态应停止。

可恢复状态不应停止，应进入入口扫描流程：

```text
企业微信在前台
-> 截图/OCR
-> 如果已经是智能总结输入页，继续
-> 如果是企微主聊天页，扫描左侧栏/应用区/已知入口区域
-> 尝试打开智能总结
-> 点击后重新截图验证
-> 多轮仍无法进入智能总结页，才失败并保存截图/OCR
```

### 3. 修复“智能总结子窗口存在”的假阳性

当前逻辑不能把“发现 child window class/title 包含智能总结”当成页面已经可用。

必须改为：

- child window 只能作为候选线索。
- 是否允许粘贴 prompt，必须由截图/OCR 页面验证决定。
- `smart_summary_page_visible(...)` 或等价页面验证必须成为进入粘贴阶段的硬条件。

特别注意：类似下面的逻辑是不合格的：

```python
if child is not None or smart_summary_page_visible(...):
    return success
```

应改为：

```python
if smart_summary_page_visible(...):
    return success
```

如果 child 存在但页面不可见，应继续入口扫描，而不是直接失败。

### 4. 企业微信主页面应作为入口扫描起点

当 OCR 显示企业微信主窗口/聊天列表/群聊内容时，脚本应继续尝试：

- UI Automation 搜索可见控件中的“智能总结”入口。
- OCR 在左侧导航栏/应用区限定范围内搜索“智能总结”或可接受的模糊文本。
- 使用参考项目中验证过的左侧入口坐标/比例作为低优先级 fallback。
- 每次点击候选入口前确认企业微信仍在前台。
- 每次点击后重新截图/OCR 验证是否进入智能总结输入页。

入口点击不应扩大到不可控全屏随机扫描。

### 5. 危险动作前仍需强校验

以下动作前必须同时满足：

- 前台窗口是企业微信。
- 当前页面已验证为智能总结输入页。

危险动作包括：

- 粘贴 prompt。
- 点击“开始总结”。
- 使用 Ctrl+A / Ctrl+C。
- 点击“复制”。
- 使用任何复制 fallback。

## 建议状态机

```text
start
-> find_wecom_window
   -> not found: fail
-> ensure_wecom_foreground(max_attempts=3)
   -> failed: fail
-> capture_and_ocr
-> if smart_summary_page_visible:
      paste_prompt
   else:
      open_smart_summary_entry_with_retries
      -> verify smart_summary_page_visible
      -> failed: fail with screenshots/OCR
-> paste_prompt
-> click_start
-> wait
-> copy_result
-> write output
```

## 验收标准

- 当前前台不是企业微信时，脚本会尝试多次恢复/置前企业微信，而不是立即失败。
- 多次恢复失败后才停止，并说明尝试失败的阶段和原因。
- 当前前台是企业微信但页面是聊天主界面时，脚本继续扫描智能总结入口。
- 发现“智能总结”子窗口不再被视为已进入智能总结输入页。
- 粘贴 prompt 前必须通过智能总结页面 OCR 验证。
- 不会把 prompt 输入到 Codex、终端、浏览器或企业微信普通聊天输入框。
- 入口扫描失败时保存截图/OCR，说明尝试过的策略。
- `--manual-input` 仍然可用。
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` 通过。
- 手动输入模式 Markdown/JSON 输出测试通过。

## 测试要求

最低测试：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
```

手动模式：

```powershell
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --output outputs\wecom_summary_manual_test.md `
  --output-json outputs\wecom_summary_manual_test.json
```

实机自动化测试场景：

1. Codex 或终端当前在前台，企业微信在后台但已打开。
   - 期望：脚本尝试把企业微信调到前台。
2. 企业微信在前台，但停留在聊天主界面。
   - 期望：脚本扫描并点击智能总结入口。
3. 企业微信存在疑似智能总结子窗口，但截图仍是聊天主界面。
   - 期望：不把 child window 当作成功，继续入口扫描。
4. 企业微信无法调到前台。
   - 期望：多轮失败后停止，不发送输入。
5. 已进入智能总结输入页。
   - 期望：脚本粘贴 prompt、点击开始总结、等待并复制结果。

自动化测试必须由用户在本机监督下进行。

## 风险提醒

- 不要为了“更自动”而取消危险动作前的页面校验。
- 不要对整个屏幕做无边界随机点击。
- 不要把企业微信主聊天页当成失败终点；它是入口扫描起点。
- 不要把“智能总结子窗口存在”当成页面可用。
- 不要承诺该能力稳定、无人值守、跨平台或适配所有企业微信 UI。

## 补充要求：处理智能总结历史结果页

用户最新测试发现，脚本已经能进入“智能总结”应用，但最终仍失败。截图显示当前页面不是初始化输入页，而是智能总结历史结果页：

- 左上角标题为“智能总结 AI+”。
- 左侧列表中已有历史总结会话。
- 主区域展示的是上一次生成的总结正文。
- 左上会话列表附近存在 `+` 新建按钮。
- 页面底部有“新建文档 / 发送邮件 / 复制”等结果操作，而不是 prompt 输入框和“开始总结”按钮。

这说明智能总结至少存在三类状态，脚本必须区分：

1. `main_chat_page`：企业微信主聊天/联系人/群列表页面。
2. `smart_summary_input_page`：智能总结初始化或新建输入页，可以粘贴 prompt 并点击“开始总结”。
3. `smart_summary_history_result_page`：智能总结历史结果页，显示旧结果，不能直接粘贴 prompt。

当前脚本不应把 `smart_summary_history_result_page` 当成失败终点。正确恢复流程是：

```text
进入智能总结应用
-> 截图/OCR
-> 如果是输入页：继续粘贴 prompt
-> 如果是历史结果页：点击左上会话列表附近的 + 新建按钮
-> 等待新建输入页出现
-> 再次截图/OCR 验证
-> 验证通过后才粘贴 prompt
```

### 历史结果页识别建议

可通过以下特征判断：

- OCR 识别到“智能总结 AI”或“智能总结”标题。
- 左侧存在历史会话条目。
- 主区域存在长篇总结正文。
- 页面底部出现“新建文档”“发送邮件”“复制”等结果操作。
- 没有识别到“输入你想总结”“开始总结”等输入页特征。

注意：历史结果页属于可恢复状态，不属于危险状态。

### 新建按钮定位建议

优先级建议：

1. UI Automation 搜索 `+` / 新建 / 新会话相关按钮。
2. OCR 或图像检测定位左上标题栏附近的 `+` 按钮。
3. 使用相对坐标 fallback：在智能总结左侧会话列表顶部、标题“智能总结 AI+”右侧附近点击。以截图为例，该按钮位于左侧列表顶部右上角，而不是主内容区。

每次点击 `+` 前仍需确认企业微信在前台；点击后必须重新截图/OCR 验证是否进入输入页。

### 输入页验证必须放宽但保持准确

输入页可能是首次初始化页，也可能是点击 `+` 后的新建页。不要只依赖某一个固定文案。

可接受输入页特征包括但不限于：

- 出现 prompt 输入区域。
- 出现“开始总结”按钮。
- 出现“输入你想总结”或类似占位文案。
- 出现“总结聊天内容”“总结团队周报”等模板入口。

只有确认进入 `smart_summary_input_page` 后，才允许粘贴 prompt。

### 更新后的状态机

```text
start
-> ensure_wecom_foreground
-> capture_and_classify_page
-> main_chat_page:
      open_smart_summary_entry_with_retries
      -> capture_and_classify_page
-> smart_summary_history_result_page:
      click_new_summary_plus
      -> wait
      -> capture_and_classify_page
-> smart_summary_input_page:
      paste_prompt
      -> click_start
      -> wait
      -> copy_result
-> unknown_page:
      save screenshot/OCR and fail after bounded retries
```

### 新增验收标准

- 如果智能总结打开后默认选中最近一次历史总结，脚本不会直接失败。
- 脚本能识别历史结果页，并点击 `+` 新建一轮智能总结。
- 点击 `+` 后必须重新验证新建输入页。
- 不能把历史总结正文当成本次采集结果直接复制。
- 不能在历史结果页直接粘贴 prompt。
- 新建按钮定位失败时，要保存截图/OCR 并说明失败阶段。
