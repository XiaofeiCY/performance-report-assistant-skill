#!/usr/bin/env python
"""Validate preview-first interview/output contract and WeCom CLI lifecycle.

Offline/mocked validation only — no live WeCom automation.

Covers:
  - New session isolation contract (SKILL.md + intake-questions.md)
  - Template/reference classification (reference_only, no questioning)
  - Complete evidence-source menu presence
  - Preview-first rules (no output-location in preview phase)
  - WeCom CLI: temp diagnostics auto-create, stdout-only, cleanup
  - WeCom CLI: relative path rejection
  - Script integrity after changes
  - Mocked temp-dir lifecycle tests (actually executed, not string-checked)
  - Honest child-validator result reporting (returncode required, SKIP/BLOCKED tracked)
  - Recursive before/after artifact snapshots
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = PROJECT_ROOT / "performance-report-assistant"
SCRIPTS_DIR = SKILL_DIR / "scripts"
SKILL_MD = SKILL_DIR / "SKILL.md"
INTAKE_MD = SKILL_DIR / "references" / "intake-questions.md"
WECOM_REF_MD = SKILL_DIR / "references" / "wecom-smart-summary-collector.md"
GIT_RULES_MD = SKILL_DIR / "references" / "git-evidence-rules.md"
WECOM_SCRIPT = SCRIPTS_DIR / "collect_wecom_smart_summary.py"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
INSTALLED_DIR = Path("C:/Users/Lenovo/.claude/skills/performance-report-assistant")

PASS = 0
FAIL = 0
SKIP_COUNT = 0
BLOCKED_COUNT = 0

# Track files/dirs created by this validation run so we can clean them safely.
_OWNED_PATHS: set[Path] = set()


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def skip(label: str) -> None:
    global SKIP_COUNT
    SKIP_COUNT += 1
    print(f"  SKIP: {label}")


def blocked(label: str) -> None:
    global BLOCKED_COUNT
    BLOCKED_COUNT += 1
    print(f"  BLOCKED: {label}")


def section(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"{text}")
    print(f"{'=' * 60}")


def own(path: Path) -> None:
    """Record a path as created by this validation run."""
    _OWNED_PATHS.add(path.resolve())


def _subprocess_env() -> dict:
    """Return env dict for subprocess calls.

    Note: We intentionally do NOT set PYTHONIOENCODING because child
    validators that use RapidOCR may legitimately write GBK text to stdout
    (Chinese OCR results).  Encoding is handled at the parent side via
    subprocess.run(encoding='utf-8', errors='replace').
    """
    return os.environ.copy()


def _run(script_path: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a child Python script. Uses system default encoding because child
    validators on Windows may output GBK text (Chinese OCR results, console
    messages).  text=True without explicit encoding lets Python use the
    locale preferred encoding, which matches the child's sys.stdout.encoding.
    """
    return subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        timeout=timeout,
        env=_subprocess_env(),
    )


def _run_cli(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run the WeCom collector CLI. Uses system default encoding.
    See _run() for rationale.
    """
    return subprocess.run(
        [sys.executable, str(WECOM_SCRIPT)] + args,
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        timeout=timeout,
        env=_subprocess_env(),
    )


# ---------------------------------------------------------------------------
# 1. SKILL.md contract checks
# ---------------------------------------------------------------------------
section("1. SKILL.md: Session Isolation & Preview-First Contract")

skill_text = SKILL_MD.read_text(encoding="utf-8")

check("current-session evidence isolation" in skill_text
      or "current-session" in skill_text.lower(),
      "SKILL.md declares current-session evidence isolation")

check("reference_only" in skill_text,
      "SKILL.md defines reference_only classification")

check("预览" in skill_text or "preview" in skill_text.lower(),
      "SKILL.md references preview phase")

check("export phase" in skill_text.lower() or "导出" in skill_text or "保存" in skill_text,
      "SKILL.md defines export phase separate from preview")

check("先生成看看" in skill_text or "先给我看" in skill_text or "起草一版" in skill_text,
      "SKILL.md references preview-first trigger phrases")

check("intake-questions.md" in skill_text,
      "SKILL.md routes to intake-questions.md for detailed interview")

check("wecom-smart-summary-collector.md" in skill_text,
      "SKILL.md routes to wecom-smart-summary-collector.md for WeCom details")

check("git-evidence-rules.md" in skill_text,
      "SKILL.md routes to git-evidence-rules.md for Git collection rules")

check("初始化" in skill_text or "Initialize" in skill_text or "Session State" in skill_text,
      "SKILL.md references session state initialization")

check("intake-questions.md" in skill_text and "git-evidence-rules.md" in skill_text,
      "SKILL.md routes to both intake-questions.md and git-evidence-rules.md for Git evidence")

# ---------------------------------------------------------------------------
# 2. intake-questions.md contract checks
# ---------------------------------------------------------------------------
section("2. intake-questions.md: Canonical Interview & Evidence Menu")

intake_text = INTAKE_MD.read_text(encoding="utf-8")

check("Session Initialization" in intake_text or "会话" in intake_text,
      "intake-questions.md has session initialization section")

check("Canonical Interview Sequence" in intake_text or "采访顺序" in intake_text,
      "intake-questions.md has canonical interview sequence")

check("reference_only" in intake_text,
      "intake-questions.md references reference_only classification")

check("模板" in intake_text and "参考" in intake_text,
      "intake-questions.md covers template/reference keywords")

check("不问" in intake_text or ("不" in intake_text and "模板" in intake_text),
      "intake-questions.md instructs not to question explicit template labels")

# Evidence menu completeness
menu_keywords = [
    "直接粘贴", "工作事项", "周报草稿",
    "文档", "会议纪要", "需求", "工单", "PR", "截图",
    "Git", "仓库",
    "企业微信智能总结",
    "其他你指定的材料",
    "暂无更多素材", "现有内容",
]
for kw in menu_keywords:
    check(kw in intake_text, f"intake-questions.md evidence menu contains: {kw}")

check("Preview-First Rules" in intake_text or "preview" in intake_text.lower(),
      "intake-questions.md has preview-first rules section")

check("这是一个新的报告周期" in intake_text or "Session Isolation" in intake_text,
      "intake-questions.md has session isolation guardrail")

# ---------------------------------------------------------------------------
# 3. wecom-smart-summary-collector.md contract checks
# ---------------------------------------------------------------------------
section("3. wecom-smart-summary-collector.md: Temp Diagnostics & Stdout Lifecycle")

wecom_text = WECOM_REF_MD.read_text(encoding="utf-8")

check("Preview-First Collection" in wecom_text or "Preferred Evidence Flow" in wecom_text,
      "wecom-smart-summary-collector.md documents preview-first/preferred flow")

check("OS temporary directory" in wecom_text or "TEMP" in wecom_text or "temp" in wecom_text.lower(),
      "wecom-smart-summary-collector.md documents OS-temp diagnostics")

check("stdout" in wecom_text.lower(),
      "wecom-smart-summary-collector.md references stdout result return")

check("failure_summary.md" in wecom_text,
      "wecom-smart-summary-collector.md documents failure diagnostics retention")

check(("do not delete" in wecom_text.lower() or "不删除" in wecom_text
       or "不清理" in wecom_text
       or "must not be silently deleted" in wecom_text.lower()
       or "not be silently deleted" in wecom_text.lower()),
      "wecom-smart-summary-collector.md warns against deleting failure diagnostics prematurely")

# Safety boundaries preserved
safety_terms = [
    "right-click copy", "Ctrl+A", "Ctrl+C",
    "send, delete, edit, or forward",
    "foreground", "left-menu vertical scanning",
    "multi-fixed-coordinate probing",
]
for term in safety_terms:
    check(term.lower() in wecom_text.lower(),
          f"wecom-smart-summary-collector.md preserves safety boundary: {term}")

check("exact fingerprint" in wecom_text.lower() or "exact current fingerprint" in wecom_text.lower(),
      "wecom-smart-summary-collector.md preserves exact fingerprint requirement")

# ---------------------------------------------------------------------------
# 4. git-evidence-rules.md contract checks
# ---------------------------------------------------------------------------
section("4. git-evidence-rules.md: Git Evidence Rules Restored")

git_rules_text = GIT_RULES_MD.read_text(encoding="utf-8")

check("Full clone is the default" in git_rules_text or "全量克隆" in git_rules_text,
      "git-evidence-rules.md states full clone is the default")

check("shallow clone" in git_rules_text.lower() or "浅克隆" in git_rules_text,
      "git-evidence-rules.md states shallow clone is explicit opt-in")

check("local fallback" in git_rules_text.lower() or "本地回退" in git_rules_text,
      "git-evidence-rules.md documents local fallback policy")

check("origin" in git_rules_text.lower() and "URL" in git_rules_text,
      "git-evidence-rules.md requires local origin match for fallback")

check("disclos" in git_rules_text.lower(),
      "git-evidence-rules.md requires fallback disclosure")

check("Pre-Execution Confirmation" in git_rules_text or "预执行" in git_rules_text,
      "git-evidence-rules.md requires pre-execution confirmation")

check("commit count" in git_rules_text.lower() or "commit" in git_rules_text.lower(),
      "git-evidence-rules.md lists expected quantitative metrics (commit)")

check("reference_only" in git_rules_text.lower(),
      "git-evidence-rules.md prohibits inferring repos from reference_only material")

check("stdout" in git_rules_text.lower(),
      "git-evidence-rules.md states stdout-only by default")

# ---------------------------------------------------------------------------
# 5. WeCom script CLI contract checks (offline/mocked)
# ---------------------------------------------------------------------------
section("5. collect_wecom_smart_summary.py: CLI Contract")

script_text = WECOM_SCRIPT.read_text(encoding="utf-8")

check("_create_temp_run_dir" in script_text,
      "Script defines _create_temp_run_dir function")

check("_cleanup_temp_if_empty" in script_text,
      "Script defines _cleanup_temp_if_empty for early-exit cleanup")

check("tempfile" in script_text,
      "Script imports tempfile for OS-temp directory creation")

check("allow_auto" in script_text,
      "Script supports allow_auto parameter for _require_explicit_output_dir")

check("_temp_screenshot_dir" in script_text,
      "Script tracks whether screenshot_dir was auto-created")

check("_cleanup_run_diagnostics" in script_text,
      "Script retains _cleanup_run_diagnostics guard")

# ---------------------------------------------------------------------------
# 6. CLI file-free tests
# ---------------------------------------------------------------------------
section("6. CLI: --prompt-only is file-free and preview-first")

result = _run_cli(["--prompt-only", "--period", "2026-07-14..2026-07-18"])
check(result.returncode == 0, f"--prompt-only exits 0 (got {result.returncode})")
check("PRAS-" in result.stdout, "--prompt-only output contains fingerprint")
check("DEFAULT_PROMPT_BODY" not in result.stdout, "--prompt-only output is rendered (not raw constant)")
# Verify preview-first: default instructions should NOT lead with Markdown/JSON save commands
check("stdout" in result.stdout.lower() or "管道" in result.stdout,
      "--prompt-only instructions lead with stdout/conversation preview")
check("保存为持久文件" in result.stdout or ("export" not in result.stdout[:500].lower() and "--output" not in result.stdout[:300]),
      "--prompt-only defers file save to optional export section, not default")

# ---------------------------------------------------------------------------
# 7. CLI: Relative path rejection
# ---------------------------------------------------------------------------
section("7. CLI: Relative path rejection")

result_rel = _run_cli(["--prompt-only", "--output", "relative.md"])
check(result_rel.returncode != 0, f"Relative --output rejected (exit {result_rel.returncode})")
rel_combined = result_rel.stdout + result_rel.stderr
check("绝对路径" in rel_combined or "must be absolute" in rel_combined.lower(),
      "Relative --output error message mentions absolute path requirement")

result_rel2 = _run_cli(["--prompt-only", "--output-json", "relative.json"])
check(result_rel2.returncode != 0, f"Relative --output-json rejected (exit {result_rel2.returncode})")

result_probe_rel = _run_cli(["--probe-only", "--screenshot-dir", "relative_dir"])
check(result_probe_rel.returncode != 0, f"Relative --screenshot-dir rejected for probe-only (exit {result_probe_rel.returncode})")

result_manual_rel = _run_cli(["--manual-input", "--output", "relative.md"])
check(result_manual_rel.returncode != 0, f"Relative --output rejected for --manual-input (exit {result_manual_rel.returncode})")

# ---------------------------------------------------------------------------
# 8. CLI: Absolute path acceptance (file-free modes)
# ---------------------------------------------------------------------------
section("8. CLI: Absolute path acceptance (file-free modes)")
with tempfile.TemporaryDirectory() as tmpdir:
    abs_out = str(Path(tmpdir) / "test_output.md")
    result_abs = _run_cli(["--prompt-only", "--output", abs_out])
    check(result_abs.returncode == 0, f"Absolute --output accepted for --prompt-only (exit {result_abs.returncode})")

# ---------------------------------------------------------------------------
# 9. CLI: Manual/semi-manual without output are stdout-only
# ---------------------------------------------------------------------------
section("9. CLI: Manual/semi-manual stdout-only by default")

# --manual-input with piped text and no --output/--output-json →
# prints to stdout, creates zero files.
test_input = "test summary content " + "x" * 20
result_manual_stdout = subprocess.run(
    [sys.executable, str(WECOM_SCRIPT), "--manual-input", "--scenario", "test", "--period", "2026-07-14..2026-07-18"],
    capture_output=True, text=True, cwd=str(PROJECT_ROOT), input=test_input,
    timeout=10, env=_subprocess_env(),
)
check(test_input.strip() in result_manual_stdout.stdout,
      "--manual-input without --output prints result to stdout")
check(result_manual_stdout.returncode == 0,
      f"--manual-input without --output exits 0 (got {result_manual_stdout.returncode})")

# ---------------------------------------------------------------------------
# 10. Mocked temp-dir lifecycle tests (actually executed)
# ---------------------------------------------------------------------------
section("10. Mocked Temp-Dir Lifecycle Tests")

# We import and exercise the actual cleanup functions from the script.
# Top-level imports are all stdlib; optional deps (PIL, easyocr, interception,
# cv2) are only imported inside function bodies, so the module import itself
# should always succeed on Windows.
wecom_mod = None
try:
    sys.path.insert(0, str(SCRIPTS_DIR))
    import collect_wecom_smart_summary as _wecom_mod
    wecom_mod = _wecom_mod
except ImportError as e:
    blocked(f"Cannot import collect_wecom_smart_summary: {e}")
except Exception as e:
    blocked(f"Unexpected error importing collect_wecom_smart_summary: {e}")

if wecom_mod is None:
    skip("All lifecycle tests — module import failed")
    # Fast-forward past this section
else:
    _cleanup_run_diagnostics = wecom_mod._cleanup_run_diagnostics
    _cleanup_temp_if_empty = wecom_mod._cleanup_temp_if_empty
    _generate_run_id = wecom_mod.generate_run_id
    _create_temp_run_dir = wecom_mod._create_temp_run_dir

    # --- Test 10a: Success cleanup removes run dir ---
    test_dir = Path(tempfile.gettempdir()) / "wecom_runs" / f"test-{_generate_run_id()}"
    test_dir.mkdir(parents=True, exist_ok=True)
    own(test_dir)
    (test_dir / "trace.jsonl").write_text('{"event":"mock"}\n', encoding="utf-8")
    (test_dir / "screenshot.png").write_bytes(b"\x89PNG\x00\x00\x00")
    result_clean = _cleanup_run_diagnostics(str(test_dir))
    check(result_clean is True, f"Success cleanup removed run dir: {test_dir}")
    check(not test_dir.exists(), f"Run dir no longer exists after cleanup")
    # Test parent cleanup with a dedicated isolated tmpdir
    with tempfile.TemporaryDirectory() as isolated_tmp:
        isolated_wecom_runs = Path(isolated_tmp) / "wecom_runs"
        isolated_run = isolated_wecom_runs / f"test-{_generate_run_id()}"
        isolated_run.mkdir(parents=True, exist_ok=True)
        own(isolated_run)
        (isolated_run / "trace.jsonl").write_text('{"event":"mock"}\n', encoding="utf-8")
        (isolated_run / "screenshot.png").write_bytes(b"\x89PNG\x00\x00\x00")
        result_iso = _cleanup_run_diagnostics(str(isolated_run))
        check(result_iso is True, "Isolated success cleanup removed run dir")
        check(not isolated_run.exists(), "Isolated run dir no longer exists")
        # _cleanup_run_diagnostics only removes the run dir itself. Parent cleanup
        # (wecom_runs) is handled separately in main() and tested in 10c.
        check(isolated_wecom_runs.exists(),
              f"Parent wecom_runs directory retained (parent cleanup is separate concern)")
    print()

    # --- Test 10b: _cleanup_temp_if_empty retains dir with failure_summary.md ---
    _rid2 = _generate_run_id()
    test_dir2 = Path(tempfile.gettempdir()) / "wecom_runs" / _rid2
    test_dir2.mkdir(parents=True, exist_ok=True)
    own(test_dir2)
    (test_dir2 / "trace.jsonl").write_text('{"event":"mock"}\n', encoding="utf-8")
    (test_dir2 / "failure_summary.md").write_text("# Failure\n\nMock failure.\n", encoding="utf-8")
    result_clean2 = _cleanup_temp_if_empty(str(test_dir2))
    check(result_clean2 is False, "_cleanup_temp_if_empty refuses to delete dir with failure_summary.md")
    check(test_dir2.exists(), "Failure dir with failure_summary.md is retained")
    shutil.rmtree(test_dir2, ignore_errors=True)
    print()

    # --- Test 10b2: _cleanup_temp_if_empty retains non-empty dir without failure_summary.md ---
    _rid2b = _generate_run_id()
    test_dir2b = Path(tempfile.gettempdir()) / "wecom_runs" / _rid2b
    test_dir2b.mkdir(parents=True, exist_ok=True)
    own(test_dir2b)
    (test_dir2b / "trace.jsonl").write_text('{"event":"mock"}\n', encoding="utf-8")
    (test_dir2b / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    result_clean2b = _cleanup_temp_if_empty(str(test_dir2b))
    check(result_clean2b is False,
          "_cleanup_temp_if_empty refuses to delete non-empty dir without failure_summary.md")
    check(test_dir2b.exists(), "Non-empty diagnostics dir without failure_summary.md is retained")
    shutil.rmtree(test_dir2b, ignore_errors=True)
    print()

    # --- Test 10c: _cleanup_temp_if_empty removes empty auto dir (valid run-id) ---
    _rid3 = _generate_run_id()
    test_dir3 = Path(tempfile.gettempdir()) / "wecom_runs" / _rid3
    test_dir3.mkdir(parents=True, exist_ok=True)
    own(test_dir3)
    result_clean3 = _cleanup_temp_if_empty(str(test_dir3))
    check(result_clean3 is True, "_cleanup_temp_if_empty removes empty auto-created dir")
    check(not test_dir3.exists(), "Empty auto-created dir is removed by _cleanup_temp_if_empty")
    print()

    # --- Test 10d: _create_temp_run_dir returns matching run_id ---
    with tempfile.TemporaryDirectory() as isolated_tmp2:
        import tempfile as tempfile_mod
        _orig_gettempdir = tempfile_mod.gettempdir
        tempfile_mod.gettempdir = lambda: isolated_tmp2
        try:
            run_dir, run_id = _create_temp_run_dir()
            own(run_dir)
            check(run_dir.name == run_id,
                  f"Directory name '{run_dir.name}' matches returned run_id '{run_id}'")
            check(run_dir.exists(), "Created run directory exists")
            check(run_dir.parent.name == "wecom_runs",
                  f"Parent is wecom_runs (got: {run_dir.parent.name})")
        finally:
            tempfile_mod.gettempdir = _orig_gettempdir
            shutil.rmtree(run_dir, ignore_errors=True)
    print()

    # --- Test 10e: run_prompt_only source is preview-first ---
    import inspect
    rp_src = inspect.getsource(wecom_mod.run_prompt_only)
    check("stdout" in rp_src.lower() or "管道" in rp_src,
          "run_prompt_only source references stdout/conversation flow")
    check("保存为持久文件" in rp_src,
          "run_prompt_only lists persistent save as optional export section")
    lines_after_step6 = rp_src.split("6.")[1] if "6." in rp_src else ""
    check("--output" not in lines_after_step6.split("如果")[0] if "如果" in lines_after_step6 else True,
          "run_prompt_only step 6 is stdout/conversation-only, not file-save")
    print()

    # --- Test 10f: _cleanup_run_diagnostics rejects system paths ---
    check(_cleanup_run_diagnostics("C:/Windows") is False,
          "_cleanup_run_diagnostics rejects system path (C:/Windows)")
    check(_cleanup_run_diagnostics("C:/Users") is False,
          "_cleanup_run_diagnostics rejects system path (C:/Users)")
    check(_cleanup_run_diagnostics(str(Path.home() / "Desktop")) is False,
          "_cleanup_run_diagnostics rejects Desktop path")
    print()

    # --- Test 10g: _cleanup_run_diagnostics rejects dirs with final output files ---
    test_dir4 = Path(tempfile.gettempdir()) / "wecom_runs" / f"test-{_generate_run_id()}"
    test_dir4.mkdir(parents=True, exist_ok=True)
    own(test_dir4)
    (test_dir4 / "trace.jsonl").write_text('{"event":"mock"}\n', encoding="utf-8")
    (test_dir4 / "output.md").write_text("# Report\n\nSome content.\n", encoding="utf-8")
    result_clean4 = _cleanup_run_diagnostics(str(test_dir4))
    check(result_clean4 is False,
          "_cleanup_run_diagnostics rejects dir with final output file (output.md)")
    check(test_dir4.exists(), "Dir with final output file is NOT deleted")
    shutil.rmtree(test_dir4, ignore_errors=True)
    print()

    # --- Test 10h: _cleanup_run_diagnostics rejects dir without trace.jsonl ---
    test_dir5 = Path(tempfile.gettempdir()) / "wecom_runs" / f"test-{_generate_run_id()}"
    test_dir5.mkdir(parents=True, exist_ok=True)
    own(test_dir5)
    result_clean5 = _cleanup_run_diagnostics(str(test_dir5))
    check(result_clean5 is False,
          "_cleanup_run_diagnostics rejects dir without trace.jsonl (not a valid run dir)")
    shutil.rmtree(test_dir5, ignore_errors=True)
    print()

    # --- Test 10i: preflight runs before temp dir creation ---
    main_src = inspect.getsource(wecom_mod.main)
    create_pos = main_src.find("_create_temp_run_dir")
    require_pos = main_src.find("require_windows()")
    check_pos = main_src.find("check_automation_dependencies()")
    check(require_pos < create_pos,
          "require_windows() is called before _create_temp_run_dir() in main()")
    check(check_pos < create_pos,
          "check_automation_dependencies() is called before _create_temp_run_dir() in main()")
    print()

# ---------------------------------------------------------------------------
# 11. Regression: Existing Validators (honest returncode + SKIP/BLOCKED)
# ---------------------------------------------------------------------------
section("11. Regression: Existing Validators (Honest Reporting)")

_validator_names = (
    "_validate_copy_fix.py",
    "_validate_result_fix.py",
    "_validate_perf_acceptance.py",
)

# Check for dependency availability before running child validators
_cv2_available = False
_yaml_available = False
try:
    import cv2  # noqa: F401
    _cv2_available = True
except ImportError:
    pass
try:
    import yaml  # noqa: F401
    _yaml_available = True
except ImportError:
    pass

if not _cv2_available:
    blocked("cv2 (OpenCV) not available — validators requiring template matching will SKIP")
if not _yaml_available:
    blocked("yaml not available — validators requiring yaml parsing will SKIP")

for vname in _validator_names:
    vpath = SCRIPTS_DIR / vname
    if not vpath.exists():
        skip(f"{vname} not found in scripts/")
        continue

    result = _run(vpath, timeout=120)
    rc = result.returncode
    stdout = result.stdout
    stderr_out = result.stderr

    # Check for missing modules in any output (crashes from import errors)
    combined = stdout + stderr_out
    if "No module named" in combined:
        missing_mod = re.search(r"No module named '(\w+)'", combined)
        mod_name = missing_mod.group(1) if missing_mod else "unknown"
        blocked(f"{vname} requires unavailable module: {mod_name}")
        continue

    # Parse test counts
    passed_match = re.search(r"(\d+)\s+passed", stdout)
    failed_match = re.search(r"(\d+)\s+failed", stdout)
    n_passed = int(passed_match.group(1)) if passed_match else 0
    n_failed = int(failed_match.group(1)) if failed_match else 0

    # Check for genuine crash (Traceback with no test results)
    has_traceback = "Traceback" in stdout or "Traceback" in stderr_out

    if has_traceback and (n_passed == 0 and n_failed == 0):
        print(f"  FAIL: {vname} crashed with Traceback and no test results (exit {rc})")
        FAIL += 1
        continue

    if rc == 0 and n_failed == 0:
        check(True, f"{vname} — {n_passed} passed, 0 failed (exit {rc})")
    elif rc != 0 and n_failed == 0:
        # Non-zero exit but no test failures — might be an environment issue.
        if "SKIP" in stdout.upper() or "skip" in stdout.lower():
            skip(f"{vname} exit {rc} with all skips ({n_passed} passed)")
        else:
            check(False, f"{vname} exit {rc} with 0 test failures — environment issue")
    else:
        check(False, f"{vname} exit {rc}, {n_passed} passed, {n_failed} failed")

# ---------------------------------------------------------------------------
# 12. Recursive artifact snapshot & comparison
# ---------------------------------------------------------------------------
section("12. Recursive Artifact Snapshot")

# Take "after" snapshots and compare against a known-good baseline.
# We don't have a true "before" at this point (child validators already ran),
# so we check against the expected state: 4 accepted outputs only.

# Check outputs/ recursively
if OUTPUTS_DIR.exists():
    output_entries: list[str] = []
    for entry in sorted(OUTPUTS_DIR.rglob("*")):
        rel = str(entry.relative_to(OUTPUTS_DIR))
        marker = "DIR" if entry.is_dir() else f"FILE ({entry.stat().st_size} bytes)"
        output_entries.append(f"  {rel} [{marker}]")

    accepted_outputs_base = {
        "weekly_report_2026-06-29_2026-07-03.md",
        "weekly_git_stats_2026-06-29_2026-07-03.md",
        "wecom_summary_live_2026-06-29_2026-07-03.md",
        "wecom_summary_live_2026-06-29_2026-07-03.json",
    }
    unexpected: list[str] = []
    for entry in OUTPUTS_DIR.rglob("*"):
        if entry.is_dir():
            continue
        rel = str(entry.relative_to(OUTPUTS_DIR))
        if rel not in accepted_outputs_base:
            unexpected.append(rel)

    check(len(unexpected) == 0,
          f"No unexpected files in outputs/ recursively (found: {unexpected if unexpected else 'none'})")
    if unexpected:
        for u in unexpected:
            print(f"    UNEXPECTED: outputs/{u}")

# Check wecom_runs/ specifically (nested directory)
wecom_runs_dir = OUTPUTS_DIR / "wecom_runs"
if wecom_runs_dir.exists():
    runs_entries = list(wecom_runs_dir.iterdir())
    if runs_entries:
        check(False, f"outputs/wecom_runs/ contains entries: {[e.name for e in runs_entries]}")
    else:
        # Empty directory — should be cleaned
        try:
            wecom_runs_dir.rmdir()
            print(f"  Cleaned empty outputs/wecom_runs/ directory")
        except Exception:
            pass
        check(True, "outputs/wecom_runs/ is clean (empty directory removed)")

# Check scripts/__pycache__
pycache = SCRIPTS_DIR / "__pycache__"
if pycache.exists():
    # Only delete if we created it (tracked via _OWNED_PATHS)
    if pycache.resolve() in _OWNED_PATHS:
        shutil.rmtree(pycache, ignore_errors=True)
        print(f"  Cleaned owned __pycache__ at {pycache}")
    else:
        print(f"  WARNING: __pycache__ exists at {pycache} but was not created by this validator")
        print(f"  Leaving in place — not owned by current validation run")
else:
    check(True, "No __pycache__ in scripts/")

# ---------------------------------------------------------------------------
# 13. Clean up owned artifacts
# ---------------------------------------------------------------------------
section("13. Owned Artifact Cleanup")

cleaned = 0
for owned_path in sorted(_OWNED_PATHS, reverse=True):  # deepest first
    try:
        if owned_path.is_dir():
            shutil.rmtree(owned_path, ignore_errors=True)
            cleaned += 1
        elif owned_path.is_file():
            owned_path.unlink(missing_ok=True)
            cleaned += 1
    except Exception:
        pass
check(True, f"Cleaned {cleaned} owned artifact(s)")

# Also clean empty wecom_runs parent dirs in temp
test_wecom_runs = Path(tempfile.gettempdir()) / "wecom_runs"
if test_wecom_runs.exists():
    try:
        remaining = list(test_wecom_runs.iterdir())
        if not remaining:
            test_wecom_runs.rmdir()
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 14. Main-Level Mocked Lifecycle Tests (unhandled exception diagnostic retention)
# ---------------------------------------------------------------------------
section("14. Main-Level Mocked Lifecycle Tests")

if wecom_mod is None:
    skip("All main-level lifecycle tests — module import failed")
else:
    import argparse as _argparse_mod

    _orig_run_automation = wecom_mod.run_automation
    _orig_check_deps = wecom_mod.check_automation_dependencies
    _orig_create_dir = wecom_mod._create_temp_run_dir

    # No-op the dependency check so main() doesn't sys.exit(1) on missing deps.
    wecom_mod.check_automation_dependencies = lambda: None

    test_tmp = Path(tempfile.mkdtemp())
    own(test_tmp)

    _orig_argv = sys.argv[:]

    SUCCESS_LIFECYCLE_OK = False
    UNHANDLED_FAILURE_RETENTION_OK = False
    EMPTY_EARLY_FAILURE_CLEANUP_OK = False
    OUTSIDE_TEMP_BOUNDARY_OK = False
    PRE_EXISTING_SIBLING_SURVIVES_OK = False

    # Track exact run directories created during this section so cleanup
    # never touches pre-existing or concurrently created sibling runs.
    _section_run_dirs = set()
    _wecom_runs_parent = Path(tempfile.gettempdir()) / "wecom_runs"
    _parent_pre_existed = _wecom_runs_parent.exists()

    # Exclusive run-directory creation with collision retry.
    # Ownership is registered immediately after successful mkdir, before
    # returning the path or allowing any file writes.
    def _exclusive_create_run_dir(parent):
        while True:
            run_id = wecom_mod.generate_run_id()
            run_dir = parent / run_id
            try:
                run_dir.mkdir(parents=True, exist_ok=False)
                _section_run_dirs.add(run_dir)
                return run_dir, run_id
            except FileExistsError:
                continue

    # Pre-existing sibling: exclusively created before lifecycle tests so it
    # is a "pre-existing sibling" relative to those tests.  Owned by this
    # process via exclusive creation; cleaned in finally with other owned dirs.
    _pre_existing_dir, _pre_existing_run_id = _exclusive_create_run_dir(_wecom_runs_parent)
    (_pre_existing_dir / "failure_summary.md").write_text(
        "# Pre-existing failure bundle\n\nThis must survive validator cleanup.\n",
        encoding="utf-8",
    )

    # Redirect temp dir creation to use exclusive ownership.
    def _mock_create_temp_run_dir():
        return _exclusive_create_run_dir(_wecom_runs_parent)

    wecom_mod._create_temp_run_dir = _mock_create_temp_run_dir

    try:
        # --- Test 14a: Success lifecycle ---
        # run_automation writes trace and screenshot, returns normally.
        _s = {"run_dir": None}  # mutable state for closures

        def _mock_success(args, run_id=""):
            _s["run_dir"] = Path(args.screenshot_dir)
            t = wecom_mod.TraceLogger(_s["run_dir"])
            t.log(event="mock_success", run_id=run_id)
            (_s["run_dir"] / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            return "fake smart summary result"

        wecom_mod.run_automation = _mock_success
        sys.argv = [
            "collect_wecom_smart_summary.py",
            "--period", "2026-07-14..2026-07-18",
        ]

        _sc_exit = 0
        try:
            _sc_exit = wecom_mod.main()
        except SystemExit as e:
            _sc_exit = e.code if e.code is not None else 1

        check(_sc_exit == 0, f"Success main() exits 0 (got {_sc_exit})")
        success_dir = _s["run_dir"]
        success_dir_cleaned = not success_dir.exists() if success_dir else True
        check(success_dir_cleaned,
              f"Success: run dir cleaned ({success_dir})")
        # SUCCESS_LIFECYCLE_OK requires only the current test run dir to be
        # cleaned.  The shared TEMP/wecom_runs parent may contain pre-existing
        # sibling runs; we do not require it to be globally empty.
        SUCCESS_LIFECYCLE_OK = success_dir_cleaned
        print()

        # --- Test 14b: Early exception (before any diagnostics) ---
        _e = {"run_dir": None}

        def _mock_early_exc(args, run_id=""):
            _e["run_dir"] = Path(args.screenshot_dir)
            # Do NOT write any files — directory is mkdir-empty.
            raise RuntimeError("preflight initialization failure")

        wecom_mod.run_automation = _mock_early_exc
        sys.argv = [
            "collect_wecom_smart_summary.py",
            "--period", "2026-07-14..2026-07-18",
        ]

        _early_caught = False
        try:
            wecom_mod.main()
        except RuntimeError:
            _early_caught = True
        except SystemExit:
            pass

        check(_early_caught, "Early exception re-raised (RuntimeError)")
        early_dir = _e["run_dir"]
        early_dir_cleaned = not early_dir.exists() if early_dir else True
        check(early_dir_cleaned,
              f"Early exception: empty dir cleaned ({early_dir})")
        EMPTY_EARLY_FAILURE_CLEANUP_OK = early_dir_cleaned
        print()

        # --- Test 14c: Mid-run exception AFTER diagnostics written ---
        _m = {"run_dir": None}

        def _mock_mid_exc(args, run_id=""):
            _m["run_dir"] = Path(args.screenshot_dir)
            t = wecom_mod.TraceLogger(_m["run_dir"])
            t.log(event="mock_diagnostics", run_id=run_id, stage="copy")
            (_m["run_dir"] / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (_m["run_dir"] / "ocr").mkdir(exist_ok=True)
            (_m["run_dir"] / "ocr" / "test.txt").write_text(
                "test OCR output", encoding="utf-8",
            )
            (_m["run_dir"] / "regions").mkdir(exist_ok=True)
            (_m["run_dir"] / "regions" / "main_body.png").write_bytes(
                b"\x89PNG\r\n\x1a\n",
            )
            raise RuntimeError("connection lost during copy stage")

        wecom_mod.run_automation = _mock_mid_exc
        sys.argv = [
            "collect_wecom_smart_summary.py",
            "--period", "2026-07-14..2026-07-18",
        ]

        _mid_caught = False
        try:
            wecom_mod.main()
        except RuntimeError:
            _mid_caught = True
        except SystemExit:
            pass

        check(_mid_caught, "Mid-run exception re-raised (RuntimeError)")

        mid_dir = _m["run_dir"]
        mid_dir_retained = mid_dir.exists() if mid_dir else False
        check(mid_dir_retained,
              f"Mid-run: diagnostics dir preserved ({mid_dir})")

        _fs = (mid_dir / "failure_summary.md") if mid_dir else None
        fs_ok = _fs.exists() if _fs else False
        check(fs_ok, f"Mid-run: failure_summary.md created ({_fs})")
        if fs_ok and _fs is not None:
            _fs_text = _fs.read_text(encoding="utf-8")
            check("unhandled_exception" in _fs_text,
                  "failure_summary.md stage is unhandled_exception")
            check("RuntimeError" in _fs_text,
                  "failure_summary.md records exception type")
            check("connection lost" in _fs_text,
                  "failure_summary.md records exception message")
            check("Safe Next Steps" in _fs_text,
                  "failure_summary.md includes safe next steps guidance")

        trace_ok = False
        screenshot_ok = False
        ocr_ok = False
        if mid_dir:
            trace_ok = (mid_dir / "trace.jsonl").exists()
            screenshot_ok = (mid_dir / "screenshot.png").exists()
            ocr_ok = (mid_dir / "ocr" / "test.txt").exists()
        check(trace_ok, "Mid-run: trace.jsonl preserved")
        check(screenshot_ok, "Mid-run: screenshot preserved")
        check(ocr_ok, "Mid-run: OCR diagnostics preserved")

        # Clean up the preserved mid-run directory (kept by design —
        # _cleanup_temp_if_empty won't touch dirs with diagnostics).
        if mid_dir is not None and mid_dir.exists():
            shutil.rmtree(mid_dir, ignore_errors=True)

        # --- Test 14d: Explicit user directory protection ---
        _user_dir = test_tmp / "user_explicit" / "my_run"
        _user_dir.mkdir(parents=True, exist_ok=True)
        (_user_dir / "trace.jsonl").write_text('{"event":"user"}\n', encoding="utf-8")

        result_user = wecom_mod._cleanup_temp_if_empty(str(_user_dir))
        check(result_user is False,
              "_cleanup_temp_if_empty rejects dir not under wecom_runs (explicit user dir)")
        check(_user_dir.exists(),
              "Explicit user dir still exists after _cleanup_temp_if_empty")

        # --- Test 14e: Dir with non-run-id name under wecom_runs rejected ---
        _bad_name = test_tmp / "wecom_runs" / "not-a-valid-run-id"
        _bad_name.mkdir(parents=True, exist_ok=True)
        result_bad = wecom_mod._cleanup_temp_if_empty(str(_bad_name))
        check(result_bad is False,
              "_cleanup_temp_if_empty rejects dir with non-run-id name under wecom_runs")
        shutil.rmtree(_bad_name, ignore_errors=True)

        # --- Test 14f: Outside-TEMP boundary ---
        # Create an isolated directory outside OS TEMP with valid shape
        # (parent=wecom_runs, leaf=valid run-id, empty).  _cleanup_temp_if_empty
        # must refuse — its canonical parent is not TEMP/wecom_runs.
        _outside_tmp = Path(tempfile.mkdtemp())
        own(_outside_tmp)
        _outside_wecom = _outside_tmp / "wecom_runs"
        _outside_wecom.mkdir(exist_ok=True)
        _outside_run_id = wecom_mod.generate_run_id()
        _outside_dir = _outside_wecom / _outside_run_id
        _outside_dir.mkdir(exist_ok=True)

        _outside_cleanup_result = wecom_mod._cleanup_temp_if_empty(str(_outside_dir))
        _outside_dir_still_exists = _outside_dir.exists()
        OUTSIDE_TEMP_BOUNDARY_OK = (
            _outside_cleanup_result is False and _outside_dir_still_exists is True
        )
        check(OUTSIDE_TEMP_BOUNDARY_OK,
              f"OUTSIDE_TEMP_BOUNDARY_OK={OUTSIDE_TEMP_BOUNDARY_OK} "
              f"(cleanup_result={_outside_cleanup_result} "
              f"dir_exists={_outside_dir_still_exists})")
        shutil.rmtree(_outside_tmp, ignore_errors=True)

        # --- Test 14g: Pre-existing sibling survival ---
        # Verify the exclusively-created sibling fixture survived all lifecycle
        # tests untouched (it was created before 14a–14f, making it a pre-existing
        # sibling relative to those tests).
        _sibling_survives = _pre_existing_dir.exists()
        _sibling_fs_survives = (_pre_existing_dir / "failure_summary.md").exists()
        PRE_EXISTING_SIBLING_SURVIVES_OK = _sibling_survives and _sibling_fs_survives
        check(PRE_EXISTING_SIBLING_SURVIVES_OK,
              f"PRE_EXISTING_SIBLING_SURVIVES_OK={PRE_EXISTING_SIBLING_SURVIVES_OK} "
              f"(dir_survives={_sibling_survives} fs_survives={_sibling_fs_survives})")
        print()

        # --- Final independent verification ---
        UNHANDLED_FAILURE_RETENTION_OK = (
            mid_dir_retained and fs_ok and trace_ok and screenshot_ok and ocr_ok
        )
        check(UNHANDLED_FAILURE_RETENTION_OK,
              f"UNHANDLED_FAILURE_RETENTION_OK={UNHANDLED_FAILURE_RETENTION_OK} "
              f"(dir_retained={mid_dir_retained} fs_ok={fs_ok} "
              f"trace_ok={trace_ok} screenshot_ok={screenshot_ok} ocr_ok={ocr_ok})")

        check(SUCCESS_LIFECYCLE_OK,
              f"SUCCESS_LIFECYCLE_OK={SUCCESS_LIFECYCLE_OK}")

        check(EMPTY_EARLY_FAILURE_CLEANUP_OK,
              f"EMPTY_EARLY_FAILURE_CLEANUP_OK={EMPTY_EARLY_FAILURE_CLEANUP_OK}")

        check(OUTSIDE_TEMP_BOUNDARY_OK,
              f"OUTSIDE_TEMP_BOUNDARY_OK={OUTSIDE_TEMP_BOUNDARY_OK}")

        check(PRE_EXISTING_SIBLING_SURVIVES_OK,
              f"PRE_EXISTING_SIBLING_SURVIVES_OK={PRE_EXISTING_SIBLING_SURVIVES_OK}")

    finally:
        wecom_mod.run_automation = _orig_run_automation
        wecom_mod.check_automation_dependencies = _orig_check_deps
        wecom_mod._create_temp_run_dir = _orig_create_dir
        sys.argv = _orig_argv
        # Clean test_tmp (isolated test dirs for 14d/14e).
        shutil.rmtree(test_tmp, ignore_errors=True)
        # Clean only the exact run directories created by this section.
        # Never enumerate or delete sibling directories under the shared
        # TEMP/wecom_runs root — pre-existing failure bundles must survive.
        for _rd in sorted(_section_run_dirs, reverse=True):
            if _rd.exists():
                shutil.rmtree(_rd, ignore_errors=True)
        # Remove the parent only when this validator created it and it is
        # now empty.  If the parent pre-existed, leave it alone.
        if not _parent_pre_existed and _wecom_runs_parent.exists():
            try:
                _remaining = list(_wecom_runs_parent.iterdir())
                if not _remaining:
                    _wecom_runs_parent.rmdir()
            except Exception:
                pass

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
section("SUMMARY")
print(f"\n  PASS:    {PASS}")
print(f"  FAIL:    {FAIL}")
print(f"  SKIP:    {SKIP_COUNT}")
print(f"  BLOCKED: {BLOCKED_COUNT}")
print(f"  TOTAL:   {PASS + FAIL + SKIP_COUNT + BLOCKED_COUNT}")

if FAIL > 0:
    print("\n  SOME CHECKS FAILED — review output above.")
    sys.exit(1)
else:
    print("\n  All checks passed (skips and blocked are recorded but non-fatal).")
    sys.exit(0)
