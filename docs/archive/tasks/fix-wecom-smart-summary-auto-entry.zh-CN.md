# 任务：修复企微智能总结自动化入口，脚本应自行唤起并进入智能总结

## 一、背景

Claude 已实现 `performance-report-assistant/scripts/collect_wecom_smart_summary.py`，但用户测试失败。

失败表现：

- 脚本启动后 OCR 未识别到“开始总结”按钮。
- 当前实现要求用户提前打开企业微信并进入“智能总结”界面。
- 如果企业微信没有处于显示器最上层，脚本不会主动把企业微信唤起到最前。
- 脚本不会自行打开“智能总结”入口。

用户的真实期望是：

> 我希望的是，自行找到企微，自行进入智能总结，自行输入提示词，自行触发。我只关心最终给我答案。如果企微没有处于显示器最上层，就点开企微使其放置到最顶层。

因此，当前实现选择了原任务文档中的“策略 A：要求用户先打开智能总结界面”，但用户实际需要的是更自动化的“策略 B：脚本也尝试打开智能总结入口”，并且要补齐窗口唤起/置顶能力。

## 二、当前问题定位

当前脚本关键问题：

1. `find_smart_summary()` 只枚举已有的 `WeWorkWindow` 子窗口，并查找 class/title 中包含“智能总结”的窗口。
2. `run_automation()` 第一步就是找智能总结窗口：

```python
main_hwnd, main_rect, _child_hwnd, _child_rect = find_smart_summary()
if not main_hwnd:
    print("企微采集失败：未找到企业微信窗口或智能总结界面。")
    print("请确认：企业微信已登录且智能总结界面已打开。")
    sys.exit(1)
```

3. 如果企微主窗口存在但没有打开智能总结界面，脚本直接失败。
4. 如果企微被其他窗口遮挡或最小化，脚本没有先恢复、聚焦、置顶。
5. 文档 `performance-report-assistant/references/wecom-smart-summary-collector.md` 也写着“需要 Windows + 企微已打开智能总结界面”，这与用户期望冲突。

## 三、目标

将企微智能总结采集器从“要求用户先进入智能总结界面”升级为：

1. 自行查找企业微信 Windows 客户端。
2. 如果企业微信不在最上层，恢复并聚焦企业微信窗口。
3. 如果企业微信最小化，恢复窗口。
4. 自行尝试打开“智能总结”入口。
5. 自行输入采集提示词。
6. 自行点击“开始总结”。
7. 自行等待结果、复制结果、输出 Markdown/JSON。
8. 用户只关心最终采集结果；除非安全确认、登录状态或无法识别入口，否则不要要求用户手动进入智能总结。

## 四、范围

建议修改：

- `performance-report-assistant/scripts/collect_wecom_smart_summary.py`
- `performance-report-assistant/references/wecom-smart-summary-collector.md`
- `performance-report-assistant/SKILL.md` 中企微采集前置条件描述，如当前仍要求用户必须先进入智能总结界面
- `performance-report-assistant/references/intake-questions.md` 中企微采集确认提示，如当前仍要求用户必须先进入智能总结界面

不要修改：

- 仓库统计逻辑。
- Excel 模板填写逻辑。
- 旧周报结构参考逻辑。
- 与企微无关的报告生成规则。

## 五、必须实现的行为

### 1. 查找并唤起企业微信主窗口

脚本应能找到企业微信 Windows 客户端主窗口。

建议：

- 枚举 `WeWorkWindow`。
- 记录窗口标题、class、rect、visible/minimized 状态。
- 如果有多个候选窗口，优先选择：
  - 可见窗口；
  - 面积较大的主窗口；
  - 当前前台窗口；
  - 标题或子控件中更像主界面的窗口。

必须支持：

- 如果窗口最小化，调用 Win32 API 恢复。
- 调用 `SetForegroundWindow` / `ShowWindow` / `BringWindowToTop` / 必要时 `AttachThreadInput` 等方式将企微放到前台。
- 如果普通 Win32 聚焦失败，可以使用 Interception 点击任务栏或窗口可见区域作为 fallback，但不要做大范围不可控点击。

### 2. 如果企微不在最上层，置顶到前台

执行采集前必须保证企业微信窗口在最前方、可截图、无遮挡。

进度提示示例：

```text
企微采集进度：正在查找企业微信主窗口。
企微采集进度：企业微信已找到，正在恢复并置于前台。
```

如果无法置顶：

```text
企微采集失败：无法将企业微信窗口置于前台。请手动点击企业微信窗口后重试，或改用手动输入模式。
```

### 3. 自行打开智能总结入口

如果没有发现智能总结界面，脚本不能立即失败。

应尝试在企业微信主窗口中通过 OCR/截图定位并打开“智能总结”入口。

建议流程：

1. 截图企业微信主窗口。
2. OCR 识别“智能总结”文本。
3. 如果识别到，点击入口。
4. 等待智能总结界面出现。
5. 再执行输入 prompt 和点击“开始总结”。

如果 OCR 未识别到完整“智能总结”，可以尝试：

- 识别“总结”；
- 识别可能的智能总结入口区域；
- 参考 `E:\work\AgentsShare\wecom_uia_probe\stage3_v2.py` 中已跑通的入口定位经验；
- 参考已有探针截图/OCR 策略。

注意：

- 不要为了打开入口做大范围随机点击。
- fallback 坐标必须有明确条件，例如基于窗口尺寸、已知入口区域、OCR 上下文，且必须在代码中标注为低优先级 fallback。
- 如果仍无法打开，才提示用户手动打开智能总结或使用 `--manual-input`。

### 4. 自行输入提示词并触发总结

当智能总结界面打开后，脚本应：

- 聚焦输入框；
- 粘贴 prompt；
- OCR 定位“开始总结”按钮；
- 点击“开始总结”；
- 等待结果生成；
- 点击“复制”或使用 fallback 复制；
- 输出结果。

用户不应被要求手动粘贴 prompt 或手动点击“开始总结”。

### 5. 保持安全确认，但减少不必要手工步骤

skill 主流程仍应在执行前确认：

- 用户已登录企业微信；
- 用户在电脑前监督；
- 允许截图/OCR/Interception/剪贴板；
- 脚本不会发送、删除、编辑、转发消息；
- 输出路径；
- 如果自动化失败是否允许手动降级。

但不应再要求：

- 用户必须先手动进入智能总结界面。

更合适的前置条件是：

```text
请确认你已登录企业微信，并打开了需要采集的聊天/群/范围所在界面。脚本会尝试把企业微信置于前台，并自行打开智能总结入口。
```

### 6. 失败时提供清晰阶段信息

失败信息要具体指出失败阶段：

- 找不到企业微信客户端；
- 找到了企业微信，但无法置顶；
- 找到了企业微信，但 OCR 找不到“智能总结”入口；
- 已进入智能总结，但找不到输入框；
- 已输入 prompt，但找不到“开始总结”按钮；
- 等待总结超时；
- 找不到复制按钮；
- 剪贴板为空或内容过短。

每个失败都要说明 fallback：

- 手动点击企业微信后重试；
- 手动进入智能总结后重试；
- 开启 `--debug` 查看截图；
- 使用 `--manual-input` 粘贴智能总结结果。

## 六、建议实现步骤

1. 阅读当前脚本：
   - `performance-report-assistant/scripts/collect_wecom_smart_summary.py`
2. 阅读企微探针资料，尤其是：
   - `E:\work\AgentsShare\wecom_uia_probe\README.md`
   - `E:\work\AgentsShare\wecom_uia_probe\stage3_v2.py`
   - `E:\work\AgentsShare\wecom_uia_probe\interception_test.py`
   - `E:\work\AgentsShare\wecom_uia_probe\stage3_copy.py`
3. 增加窗口查找与前台激活函数，例如：

```text
find_wecom_main_window()
restore_window()
bring_window_to_front()
capture_wecom_main_window()
open_smart_summary_entry()
wait_for_smart_summary_window()
```

4. 修改 `run_automation()` 流程：

```text
查找企微主窗口
-> 恢复/置顶企微
-> 查找是否已在智能总结界面
-> 如果不在，则尝试打开智能总结入口
-> 等待智能总结界面
-> 输入 prompt
-> 点击开始总结
-> 等待并复制结果
```

5. 更新说明文档，不再写“用户必须先进入智能总结界面”，改为“用户需登录并打开目标聊天/群/范围；脚本会尝试进入智能总结”。
6. 保留 `--manual-input` 降级模式。
7. 保留 `--debug` 截图/OCR 调试能力。

## 七、测试要求

最低测试：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
```

手动模式回归测试：

```powershell
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --output outputs\wecom_summary_manual_test.md `
  --output-json outputs\wecom_summary_manual_test.json
```

自动化测试场景：

1. 企业微信已登录，但不在最上层。
   - 期望：脚本将企业微信置于前台。

2. 企业微信已登录，停留在目标聊天/群界面，但未进入智能总结。
   - 期望：脚本自行找到并打开智能总结入口。

3. 智能总结界面已打开。
   - 期望：脚本仍能正常输入 prompt、点击开始总结、复制结果。

4. 企业微信未打开。
   - 期望：清晰提示找不到企业微信，不乱点。

5. OCR 找不到智能总结入口。
   - 期望：停止自动化并提示开启 `--debug` 或手动模式。

自动化测试必须在用户监督下进行。

## 八、验收标准

完成后应满足：

- 脚本不再要求用户先进入智能总结界面。
- 如果企业微信存在但不在最上层，脚本会尝试恢复并置顶。
- 脚本会尝试自行打开智能总结入口。
- 脚本会自行输入 prompt。
- 脚本会自行点击“开始总结”。
- 脚本会等待并复制结果。
- 找不到入口或按钮时，失败信息明确，不继续乱点。
- `--manual-input` 仍可用。
- `--debug` 仍可保存必要截图/OCR 调试信息。
- 文档不再误导用户必须提前进入智能总结界面。
- 未修改无关功能。

## 九、安全边界

仍然禁止：

- 读取企业微信本地数据库。
- 逆向企业微信客户端。
- 调用或伪造企业微信 API。
- 自动发送消息。
- 删除、编辑、转发消息。
- 处理登录、验证码、安全弹窗。
- 绕过用户可见权限。
- 大范围随机点击。

允许：

- 恢复并置顶企业微信窗口。
- 在用户确认和监督下，通过可见 UI 打开智能总结入口。
- 通过可见 UI 粘贴 prompt。
- 通过可见 UI 点击“开始总结”。
- 通过可见 UI 点击“复制”或使用复制 fallback。

## 十、交付说明要求

Claude 完成后请说明：

- 修改了哪些文件。
- 如何查找企业微信主窗口。
- 如何恢复/置顶企业微信。
- 如何打开智能总结入口。
- 如何避免随机乱点。
- 自动化测试是否实际运行；如果没有，说明原因。
- 哪些失败场景仍需要用户手动介入。
