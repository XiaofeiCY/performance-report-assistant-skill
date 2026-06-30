# WeCom Smart Summary Collector

Enterprise WeChat Windows 客户端智能总结采集器。当前实现以 `E:/work/AgentsShare/wecom_uia_probe/stage3_v2.py` 的已验证链路为基准，通过 Win32 窗口控制、Interception 和 EasyOCR 执行分阶段采集：进入智能总结输入页、输入提示词、点击开始总结、等待结果并复制到剪贴板，最终输出标准化 Markdown 和 JSON 文件。

**当前状态：不稳定 / 待监督复测。** 该采集器不是通用企微自动化能力，也不承诺无人值守、跨平台或企业级稳定。自动化路径只支持已验证的企业微信主界面、智能总结输入页，以及智能总结历史结果页通过 `+` 新建会话回到输入页的恢复路径。未知页面必须停止并保存截图/OCR，而不是继续猜测点击。

## 功能说明

- 在 Windows 上查找、恢复并置顶企业微信客户端。
- 自行尝试打开企业微信智能总结入口，入口定位只采用 UIA/OCR 精确命中"智能总结"和单个 probe 校准坐标。
- 如果智能总结打开后默认选中最近一次历史结果，识别为历史结果页，点击左上会话列表附近的 `+` 新建本次总结，再等待输入页出现。
- 使用 Interception 驱动级输入完成窗口聚焦、点击、粘贴。
- 使用截图 + EasyOCR 定位"智能总结"入口、"开始总结""复制"等关键按钮。
- 企业微信窗口可任意伸缩，入口定位不得使用左侧纵向扫描或多绝对坐标试探。
- 在每次点击、粘贴、复制前执行安全检查，确认前台窗口仍是企业微信，避免把提示词输入到 Codex、终端、浏览器或其他窗口。
- 粘贴提示词前会二次确认智能总结界面可见。
- 智能总结生成时长不固定，等待逻辑应以可观察 UI/结果状态为主，以硬上限超时为兜底。
- 复制按钮可能在结果底部、窗口可见区域外或长结果滚动区域下方；复制流程必须先确认结果页，再通过 UIA/OCR 和有限内容区滚动查找复制按钮。
- 支持从文件读取自定义采集提示词。
- 支持 `--manual-input` 降级模式，不操作企业微信，只封装手动输入的文本。
- 输出 Markdown（含来源、采集方式、状态、原始摘要）和 JSON。

## 运行环境

- **Windows only**（自动化模式）。
- 企业微信 Windows 客户端已登录。
- Python 3.13 或兼容版本。
- Interception 驱动已安装并重启（自动化模式）。
- EasyOCR / numpy / pillow / pyperclip（pip 安装）。

## 企业微信客户端前置状态

自动化模式运行前：

1. 登录企业微信 Windows 客户端。
2. 打开目标聊天或目标范围所在界面；如果已经进入智能总结历史结果页，也可以作为恢复点，但脚本需要先点击 `+` 新建本次总结。
3. 用户正在电脑旁监督。
4. 脚本会尝试将企业微信置于前台，并按 probe 验证过的入口坐标/OCR 路径进入智能总结；如进入历史结果页，应新建会话后再进入输入页。

不强制要求用户预先进入智能总结界面，但当前自动化仍不稳定。若入口定位、历史结果页新建、或输入页验证失败，脚本会停止并保存阶段截图/OCR；建议改用 `--manual-input`，或由用户手动进入智能总结输入页后再重试。

## Interception 依赖

Interception 驱动和 Python 模块不是普通 pip 依赖：

- 驱动需要从 GitHub 下载安装并重启系统。
- Python 模块需要单独安装和验证。
- 不能承诺换一台机器直接可用。
- 不能承诺 macOS 可用。

## 运行命令示例

### 查看帮助

```powershell
python scripts/collect_wecom_smart_summary.py --help
```

### 自动化模式（需要 Windows + 企微已登录并打开目标界面）

```powershell
python scripts/collect_wecom_smart_summary.py `
  --scenario production-fix `
  --period "2026-06-22..2026-06-26" `
  --output outputs/wecom_summary.md `
  --output-json outputs/wecom_summary.json
```

调试模式：

```powershell
python scripts/collect_wecom_smart_summary.py --debug --output outputs/wecom_summary.md
```

自动化模式会保留阶段截图和 OCR 文本，便于验收和定位问题。`--debug` 当前仅作为兼容参数保留。

### 手动降级模式

从 stdin 输入：

```powershell
echo "智能总结内容..." | python scripts/collect_wecom_smart_summary.py `
  --manual-input --output outputs/wecom_summary.md --output-json outputs/wecom_summary.json
```

从剪贴板读取：

```powershell
python scripts/collect_wecom_smart_summary.py `
  --manual-input --from-clipboard `
  --output outputs/wecom_summary.md `
  --output-json outputs/wecom_summary.json
```

### 自定义提示词

```powershell
python scripts/collect_wecom_smart_summary.py `
  --prompt-file my_prompt.txt `
  --output outputs/wecom_custom.md
```

## 输出契约

### Markdown

```markdown
# Enterprise WeChat Smart Summary Evidence

- Source: wecom_smart_summary
- Collection method: desktop_automation / manual_input
- Scenario: production-fix
- Period: ...
- Status: needs_user_confirmation
- Collected at: ...

## Raw Smart Summary

...
```

### JSON

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

## 安全边界

**允许：**

- 查找、恢复并置顶企业微信窗口。
- 打开智能总结界面。
- 粘贴采集提示词。
- 点击"开始总结"。
- 等待结果生成。
- 点击已验证的"复制"按钮。
- 读取本地剪贴板。

**禁止：**

- 读取企业微信本地数据库。
- 逆向企业微信客户端。
- 调用或伪造企业微信官方 API。
- 自动发送消息。
- 删除、编辑、转发任何消息。
- 处理登录、验证码、安全弹窗。
- 绕过用户可见权限。
- 当前前台窗口不是企业微信时继续点击、粘贴或复制。
- 未确认智能总结界面可见时粘贴提示词。
- 大范围随机点击。
- 在企业微信左侧菜单栏做纵向扫描、逐项试点或来回切换入口。
- 在未知页面或未知内容区域执行右键复制、固定坐标复制、Ctrl+A/Ctrl+C 全选复制。

## 自动化安全护栏

采集器必须优先保证不误操作其他窗口：

- 前台窗口识别会检查企业微信根窗口、父窗口、owner 和进程 ID。
- 如果 Codex、终端、浏览器等窗口抢回焦点，脚本会尝试重新拉起企业微信；仍无法确认时会退出。
- 每次危险动作前都会重新确认企业微信仍在前台：
  - 点击智能总结入口；
  - 点击输入区；
  - 粘贴提示词；
  - 点击"开始总结"；
  - 点击"复制"。
- 粘贴提示词前还会 OCR 检查智能总结界面强特征，例如"智能总结"、"开始总结"、"你想总结"、"暂无历史总结"、"总结团队周报"等。
- 如果 OCR 检测到智能总结历史结果页，例如左侧历史会话、主区域旧总结正文、底部"新建文档/发送邮件/复制"等结果操作，脚本不能直接复制旧结果或粘贴 prompt，也不能回退到企业微信左侧菜单扫描；必须只尝试点击智能总结页内左上会话列表附近的 `+` 新建本次总结，并重新验证输入页。
- 等待生成过程中会输出心跳进度。固定超时只作为硬上限；是否进入复制阶段应由结果页、结果文本稳定、底部操作区或复制按钮等可观察信号决定。
- 超时后只有在仍能确认企业微信前台、智能总结结果页可见、且存在可复制结果时，才允许复制；否则必须停止并保存截图/OCR。

## Probe 基准流程

当前自动化必须对齐 `E:/work/AgentsShare/wecom_uia_probe` 的成功链路：

1. 如果已经存在 class/title 包含"智能总结"的企业微信子窗口，仍必须截图/OCR 分类页面，不能仅凭子窗口存在进入粘贴阶段。
2. 如果不存在智能总结子窗口，先截取企业微信窗口，尝试通过 UIA/OCR 精确定位左侧"智能总结"入口。
3. 如果 OCR 未命中，最多只允许使用 probe 文档中验证过的单个左侧入口坐标作为不稳定 fallback：约 `(31, 499)`，按当前窗口高度比例缩放；禁止沿左侧菜单逐项扫描或多点试探。
4. 入口点击后必须截图/OCR 分类页面：企微主聊天页、智能总结输入页、智能总结历史结果页、未知页。
5. 如果是历史结果页，只点击智能总结页内左上会话列表附近的 `+` 新建本次总结，等待并重新验证输入页；如果未能进入输入页，立即停止并保存截图/OCR。
6. 在输入页中点击输入区域并用 Interception 粘贴提示词。
7. OCR 定位"开始总结"按钮；未识别时使用 `stage3_v2.py` 的底部右侧按钮 fallback。
8. 轮询可观察状态：结果正文出现、文本持续增长、文本稳定、底部操作区出现、复制按钮出现、或"开始总结"消失。
9. 复制优先使用 UIA 查找"复制"按钮；其次在确认结果页后执行有限内容区滚动并 OCR 查找底部"复制"按钮。找不到时安全失败并提示手动输入，不使用右键菜单、多固定坐标或未知区域 Ctrl+A/Ctrl+C。

每个阶段都会保存截图/OCR。未确认进入智能总结输入页时，不允许粘贴提示词。

## 已验证界面边界

当前版本只支持以下已验证或明确限定的页面状态：

- 企业微信主聊天页：可作为入口扫描起点。
- 智能总结输入页：标题或侧栏中可识别"智能总结"，且页面中存在"输入你想总结的主题"、"开始总结"、"暂无历史总结"、"总结团队周报"、"总结聊天内容"等输入页特征。
- 智能总结历史结果页：标题或侧栏中可识别"智能总结"，左侧存在历史会话，主区域显示旧总结正文，底部可能存在"新建文档"、"发送邮件"、"复制"等结果操作。该状态只能用于点击 `+` 新建本次总结，不能作为本次采集结果。

如果检测到智能总结子窗口，但截图/OCR 不能确认是输入页或历史结果页，脚本会停止并保存诊断截图/OCR，不会继续尝试聊天式输入或其他未验证分支。

## 常见失败原因

| 错误 | 原因 | 解决 |
|------|------|------|
| 非 Windows 环境 | 自动化需要 Windows | 使用 `--manual-input` |
| 找不到企业微信窗口 | 客户端未打开 | 打开并登录企业微信 |
| 无法置顶企业微信 | Windows 焦点限制或窗口被遮挡 | 手动点击企业微信后重试，或使用 `--manual-input` |
| 前台窗口不是企业微信 | Codex/终端/浏览器抢回焦点 | 脚本会停止以避免误输入；手动点击企业微信后重试 |
| 找不到智能总结入口 | UIA/OCR 精确命中和单个 probe 校准坐标都未确认入口 | 查看自动保存的失败截图和 OCR 文本；不要启用左侧菜单纵向扫描 |
| 智能总结打开到历史结果页 | 企微默认选中最近一次历史总结 | 只点击智能总结页内左上 `+` 新建本次总结，验证输入页后再粘贴 prompt |
| 智能总结子窗口存在但不是输入页或历史结果页 | 当前界面不是已验证状态 | 停止自动化，查看阶段截图/OCR，决定是否新增独立验证链路 |
| 缺少 `interception` | 驱动未安装 | 安装驱动和 Python 模块 |
| 缺少 `easyocr` 等 | pip 依赖未安装 | `pip install -r requirements-wecom.txt` |
| OCR 找不到按钮 | 窗口遮挡或分辨率变化 | 调整窗口，或使用 `--debug` 检查截图 |
| 等待超时 | 总结生成太慢 | 增加 `--max-wait-seconds`；检查阶段截图确认是否仍在智能总结页 |
| 剪贴板为空 | 复制失败 | 检查阶段截图确认页面状态；如复制按钮位于底部不可见区域，手动复制或使用 `--manual-input` |
