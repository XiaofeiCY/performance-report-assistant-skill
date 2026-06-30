# Claude Code 任务文档：实现 Windows 企业微信智能总结采集器

生成日期：2026-06-29

## 一、任务背景

当前已经在 Windows 环境中跑通一条企业微信“智能总结”采集链路：

```text
Windows
-> 企业微信 Windows 客户端
-> Interception 驱动级输入
-> 截图/OCR/坐标点击
-> 打开企业微信“智能总结”
-> 输入采集提示词
-> 点击“开始总结”
-> 等待总结生成
-> 点击“复制”或 fallback 复制
-> 从剪贴板读取总结结果
```

本任务只要求在 skill 项目中实现这个“企业微信智能总结采集器”功能模块。

不要修改 skill 的主流程、采访流程、证据分析流程、报告生成流程或上下文接入逻辑。采集器后续插入到 skill 哪个位置，由用户另行指导。

## 二、当前资料来源

资料仓库路径：

```text
E:\work\AgentsShare
```

已有成功探针目录：

```text
E:\work\AgentsShare\wecom_uia_probe
```

必须优先阅读以下文件，不要凭空重写：

```text
E:\work\AgentsShare\wecom_uia_probe\README.md
E:\work\AgentsShare\wecom_uia_probe\requirements.txt
E:\work\AgentsShare\wecom_uia_probe\stage3_v2.py
E:\work\AgentsShare\wecom_uia_probe\interception_test.py
E:\work\AgentsShare\wecom_uia_probe\stage3_copy.py
```

其中：

- `stage3_v2.py` 是已成功跑通“点击开始总结、等待结果、复制总结”的主参考实现。
- `interception_test.py` 记录了为什么需要 Interception 驱动级输入，以及如何用 Interception 向智能总结输入框粘贴 prompt。
- `stage3_copy.py` 提供复制失败时的 fallback 思路。
- `requirements.txt` 记录普通 Python 包依赖。

## 三、目标仓库和目标文件

目标 skill 项目当前路径：

```text
E:\work\performance-report-assistant-skill
```

目标 skill 目录：

```text
E:\work\performance-report-assistant-skill\performance-report-assistant
```

当前已知结构：

```text
performance-report-assistant/
  SKILL.md
  references/
  scripts/
    collect_git_commits.py
    fill_excel_template.py
```

注意：当前 `E:\work\performance-report-assistant-skill` 是 git 仓库，并且可能已有用户或其他 Claude 产生的未提交改动。修改前必须先运行 `git status --short`，阅读相关文件现状，避免覆盖或回退既有改动。

当前仓库根目录可能已有：

```text
README.md
README.zh-CN.md
claude-code-skill-build-plan.md
docs/
```

本任务不要求修改这些根目录文档，也不要求修改 `SKILL.md` 的主流程。除非为了说明采集器依赖确实必须新增局部文档，否则不要扩大修改范围。

## 四、任务目标

在目标 skill 目录下实现一个独立的 Windows 企业微信智能总结采集器，建议文件名：

```text
performance-report-assistant/scripts/collect_wecom_smart_summary.py
```

该脚本应做到：

1. 在 Windows 上操作已打开的企业微信客户端智能总结界面。
2. 使用 Interception 驱动级输入完成窗口聚焦、点击、粘贴、快捷键复制等动作。
3. 使用截图和 OCR 定位“开始总结”“复制”等关键按钮。
4. 支持输入默认采集提示词或从文件读取提示词。
5. 支持等待总结生成并读取剪贴板文本。
6. 将结果输出为 Markdown 文件。
7. 可选输出 JSON 文件。
8. 支持 `--manual-input` 降级模式，不操作企业微信，只把用户粘贴或剪贴板中的智能总结文本封装成标准输出。
9. 提供清晰的 `--help`、依赖错误提示和平台错误提示。

本任务只实现采集器本身，不决定它如何接入 skill 主流程。

## 五、建议命令行接口

必须支持：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
```

必须支持：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --output outputs\wecom_summary.md
```

建议支持：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --scenario production-fix `
  --period "2026-06-22..2026-06-26" `
  --output outputs\wecom_summary.md `
  --output-json outputs\wecom_summary.json
```

必须支持手动降级模式：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --output outputs\wecom_summary_manual.md `
  --output-json outputs\wecom_summary_manual.json
```

建议支持参数：

```text
--scenario
--period
--prompt-file
--output
--output-json
--manual-input
--from-clipboard
--debug
--screenshot-dir
--timeout
--poll-interval
```

参数行为建议：

- `--scenario` 默认 `production-fix`。
- `--period` 默认空字符串或 `current_period`，不要自行推算周期。
- `--prompt-file` 指定后读取文件内容作为智能总结 prompt。
- `--manual-input` 指定后不操作企业微信。
- `--from-clipboard` 可与 `--manual-input` 搭配，从剪贴板读取文本；否则从 stdin 读取。
- `--debug` 开启后才保存截图、OCR 文本等调试文件。
- `--screenshot-dir` 默认可为 `outputs/wecom_screenshots`，但只有 `--debug` 时写入。
- `--timeout` 默认可设为 120 秒。
- `--poll-interval` 默认可设为 3 秒。

## 六、默认采集提示词

默认 prompt 已被后续修正为动态周期提示词。不得固定写"本周"；必须根据已确认的报告周期使用绝对日期或"目标周期内"。

```text
总结 [YYYY-MM-DD 至 YYYY-MM-DD] 期间聊天中涉及临时生产修数、生产数据处理、线上数据维护、业务方临时数据修正相关的事项。只列出真实发生的工作事项，按时间或事项分条。
```

如果用户通过 `--prompt-file` 提供 prompt 文件，则使用文件内容覆盖默认 prompt。

## 七、输出契约

### Markdown 输出

Markdown 文件至少包含：

```markdown
# Enterprise WeChat Smart Summary Evidence

- Source: wecom_smart_summary
- Collection method: desktop_automation
- Scenario: production-fix
- Period: ...
- Status: needs_user_confirmation
- Collected at: ...

## Raw Smart Summary

...
```

如果是手动模式，`Collection method` 应为：

```text
manual_input
```

如果实际运行了企业微信自动化，`Collection method` 应为：

```text
desktop_automation
```

### JSON 输出

如果指定 `--output-json`，JSON 至少包含：

```json
{
  "source": "wecom_smart_summary",
  "collection_method": "desktop_automation",
  "scenario": "production-fix",
  "period": "...",
  "status": "needs_user_confirmation",
  "raw_summary": "...",
  "collected_at": "...",
  "runtime": {
    "platform": "windows",
    "client": "wecom_desktop",
    "collector": "collect_wecom_smart_summary.py"
  }
}
```

手动模式时：

```json
{
  "collection_method": "manual_input"
}
```

不要在采集器中做复杂事项抽取，不要判断哪些内容可写入周报。第一版只负责可靠采集和标准化输出。

## 八、核心实现要求

请以 `stage3_v2.py` 为基础封装，但要整理成可复用 CLI，而不是直接复制实验脚本。

建议拆分函数：

```text
parse_args()
require_windows()
load_prompt()
check_dependencies()
find_wecom_windows()
find_smart_summary_window()
capture_window()
ocr_find()
ocr_all()
focus_wecom_window()
paste_prompt_with_interception()
click_start_summary()
wait_for_summary()
copy_summary_result()
read_manual_input()
write_markdown()
write_json()
main()
```

关键实现点：

1. 使用 Win32 API 枚举企业微信窗口，参考 `stage3_v2.py` 中 `WeWorkWindow` 类名识别逻辑。
2. 优先识别包含“智能总结”的子窗口或窗口标题。
3. 使用 `PIL.ImageGrab.grab(..., all_screens=True)` 截图。
4. 使用 EasyOCR 识别中文和英文：

```python
easyocr.Reader(["ch_sim", "en"])
```

5. 用 OCR 定位“开始总结”按钮。
6. 如果没有识别到完整“开始总结”，可尝试识别“总结”，并用按钮位置约束过滤。
7. 最后才允许使用明确标注的 fallback 坐标，并且只作为低优先级兜底。
8. 使用 Interception 进行鼠标移动、点击、Ctrl+V、Ctrl+C 等输入动作。
9. 等待结果时轮询 OCR 文本，检测“复制”出现或“开始总结”消失。
10. 优先点击“复制”按钮读取剪贴板。
11. 如果没有“复制”按钮，参考 `stage3_copy.py` 做 select/copy fallback。
12. 读取剪贴板后校验文本长度，过短时给出明确错误。
13. 输出目录不存在时自动创建。
14. 默认不要保存截图、OCR 明细和实验文件；只有 `--debug` 时保存。

## 九、依赖与环境要求

运行环境必须明确限制：

```text
Windows only
WeCom / 企业微信 Windows 客户端
Python 3.13 或兼容版本
Interception 驱动已安装并重启
interception Python 模块可 import
easyocr / numpy / pillow / pyperclip
```

普通 Python 依赖可参考：

```text
easyocr==1.7.2
numpy==2.4.6
pillow==12.2.0
pyperclip==1.11.0
uiautomation==2.0.29
```

注意：

- `interception` Python 模块和 Interception 驱动不是普通 pip 依赖。
- 不要承诺脚本可以自动安装 Interception 驱动。
- 不要承诺换一台 Windows 机器可直接运行。
- 不要承诺 macOS 可用。

如有必要，可以新增：

```text
performance-report-assistant/scripts/requirements-wecom.txt
```

该文件只列普通 Python 包。必须在注释或配套文档中说明 Interception 驱动需要单独安装和验证。

## 十、建议新增说明文档

建议新增：

```text
performance-report-assistant/references/wecom-smart-summary-collector.md
```

该文档只说明采集器功能本身，不要指导 skill 主流程如何接入。

内容至少包括：

- 功能说明。
- Windows-only 运行环境。
- 企业微信客户端前置状态。
- Interception 依赖。
- OCR/截图依赖。
- 运行命令示例。
- 手动降级模式。
- 输出 Markdown/JSON 契约。
- 调试模式输出说明。
- 安全边界。
- 常见失败原因。

## 十一、企业微信客户端前置状态

脚本运行前应要求用户完成：

1. 登录企业微信 Windows 客户端。
2. 打开目标聊天或目标范围所在界面。
3. 确保用户正在旁边监督。
4. 如脚本不负责打开智能总结入口，则用户需要先进入“智能总结”界面。

第一版可以选择两种实现策略之一：

### 策略 A：要求用户先打开智能总结界面

这是更稳妥的第一版。

脚本只负责：

```text
定位智能总结窗口
-> 粘贴 prompt
-> 点击开始总结
-> 等待结果
-> 复制结果
-> 输出文件
```

### 策略 B：脚本也尝试打开智能总结入口

如果实现此策略，必须复用现有探针经验，通过截图/OCR 查找“智能总结”入口，失败时清晰提示用户手动打开。

不要为了打开入口而增加大范围不可控点击。

如果不确定，优先实现策略 A。

## 十二、安全边界

本任务严禁：

- 不读取企业微信本地数据库。
- 不逆向企业微信客户端。
- 不调用或伪造企业微信官方 API。
- 不自动发送企业微信消息。
- 不删除、编辑、转发任何消息。
- 不处理登录、验证码、安全提示或安全弹窗。
- 不绕过用户可见权限。
- 不把智能总结结果直接当成事实。
- 不把讨论、风险提醒、未完成事项写成已完成工作。
- 不把能力描述成无人值守、跨平台或企业级稳定。
- 不修改 skill 的主流程接入逻辑。
- 不修改报告生成规则。
- 不修改已有 `SKILL.md` 的上下文流程，除非用户在 skill 项目中另行要求。

## 十三、失败处理要求

必须给出清晰错误信息：

- 非 Windows 环境：提示只能使用 `--manual-input`。
- 找不到企业微信窗口：提示用户打开企业微信客户端。
- 找不到智能总结窗口：提示用户先进入智能总结界面。
- 缺少 `interception`：提示需要安装 Python 模块和 Windows 驱动，并重启验证。
- 缺少 `easyocr` / `PIL` / `pyperclip`：提示安装普通 Python 依赖。
- OCR 找不到按钮：提示用户调整窗口、手动打开界面或开启 `--debug` 检查截图。
- 等待超时：保存或提示 debug 信息，不要继续乱点。
- 剪贴板为空或内容过短：提示复制失败，并建议使用 `--manual-input`。

## 十四、检查命令

至少运行：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
```

测试手动模式：

```powershell
"本周处理了业务方临时提出的生产数据修正需求，并完成线上数据核查。" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --output outputs\wecom_summary_test.md `
  --output-json outputs\wecom_summary_test.json
```

如果 PowerShell 管道中文编码异常，可改为：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --from-clipboard `
  --output outputs\wecom_summary_test.md `
  --output-json outputs\wecom_summary_test.json
```

自动化链路测试只在用户明确允许并监督企业微信客户端时运行：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --scenario production-fix `
  --period "current_period" `
  --output outputs\wecom_summary.md `
  --output-json outputs\wecom_summary.json `
  --debug
```

不要在无人监督时自动操作企业微信。

## 十五、验收标准

完成后应满足：

1. 新增 `collect_wecom_smart_summary.py`。
2. 脚本有清晰 CLI 参数和 `--help`。
3. `--manual-input` 能在不操作企业微信的情况下输出 Markdown/JSON。
4. Markdown 输出包含 source、collection method、scenario、period、status、collected at、raw summary。
5. JSON 输出包含同等核心字段。
6. 非 Windows 环境会清晰拒绝自动化模式，并提示使用手动模式。
7. 缺少依赖时有可读错误，不是直接堆栈崩溃。
8. 自动化路径复用已有探针核心逻辑：Win32 窗口识别、截图、EasyOCR、Interception 点击/快捷键、剪贴板读取。
9. 默认不产生大量截图和 OCR 文件，只有 `--debug` 时保存。
10. 新增或更新了采集器说明文档。
11. 没有修改 skill 主流程、报告生成流程或上下文接入逻辑。
12. 没有读取数据库、逆向客户端或发送消息。

## 十六、交付说明要求

Claude 完成后请回复：

- 修改或新增了哪些文件。
- 采集器的命令行参数有哪些。
- `--manual-input` 测试是否通过。
- 是否实际运行了企业微信自动化测试；如果没有，说明原因。
- 还需要用户确认哪些本机依赖，例如 Interception 驱动是否已安装、企业微信是否已打开、是否已进入智能总结界面。
- 是否存在尚未解决的限制或 fallback。

不要自动提交 commit，除非用户明确要求。

## 十七、本任务一句话总结

请在 skill 项目中实现一个独立、Windows-only、基于 Interception + OCR 的企业微信智能总结采集器，输出标准 Markdown/JSON；不要决定它如何接入 skill 主流程。
