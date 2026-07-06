# Task: Keep Screen Awake During Supervised WeCom Collection

## Background

During longer supervised WeCom Smart Summary collection runs, Windows may turn off the display or enter sleep according to the user's power settings. This can interrupt desktop automation, OCR, screenshots, template matching, foreground checks, and copy verification.

The collector is Windows desktop automation and must remain user-supervised. This task is only about temporarily requesting Windows to keep the system/display awake while the collector is running, then releasing that request at the end.

## User Need

When running supervised WeCom collection, keep the screen on and the computer awake for the duration of the collection. After the run finishes, fails, or is interrupted, restore the previous behavior by releasing the temporary keep-awake request.

## Goal

Add a low-risk Windows-only keep-awake guard around the supervised WeCom collection path.

Recommended implementation:

- Use the Windows `SetThreadExecutionState` API through Python `ctypes`.
- During the guarded collection phase, request:
  - `ES_CONTINUOUS`
  - `ES_SYSTEM_REQUIRED`
  - `ES_DISPLAY_REQUIRED`
- On exit, including errors and `KeyboardInterrupt`, release the request with `ES_CONTINUOUS`.
- Log trace events for keep-awake enable, disable, and failure.

## Scope

In scope:

- Add a small helper/context manager, preferably near the WeCom collector implementation or in a local utility module if that fits existing structure.
- Apply it only to the supervised desktop automation collection path where screen state matters.
- Ensure cleanup runs in `finally`.
- Make behavior Windows-specific and best-effort.
- Preserve current WeCom foreground/page-state safety checks.
- Add lightweight validation or unit coverage where practical.

Out of scope:

- Do not change Windows power plans with `powercfg`.
- Do not disable screen saver, lock screen policy, or corporate security policy.
- Do not simulate mouse or keyboard activity.
- Do not make the collector unattended.
- Do not change WeCom collector state machine, OCR decision logic, copy strategy, fingerprint verification, or page-safety gates.
- Do not run live WeCom full-auto tests unless the user is supervising and explicitly authorizes it in the current conversation.

## Product / Safety Boundaries

- This feature should be described as a temporary per-process Windows keep-awake request during supervised collection.
- It should not be described as permanently changing user power settings.
- It should not promise to override manual sleep, lid-close behavior, lock-screen policy, admin-managed power policy, or all hardware/driver behavior.
- If the keep-awake request fails, the collector may continue with a clear warning/trace entry, unless the implementation discovers a stronger local reason to fail fast.

## Suggested Execution Steps

1. Read `AGENTS.md`.
2. Read `docs/status.md` Current Handoff Snapshot.
3. Read `performance-report-assistant/references/wecom-smart-summary-collector.md`.
4. Inspect `performance-report-assistant/scripts/collect_wecom_smart_summary.py` and nearby helper patterns.
5. Add a Windows keep-awake context manager using `ctypes.windll.kernel32.SetThreadExecutionState`.
6. Wrap the supervised desktop automation run so cleanup always executes.
7. Add trace/log events without weakening existing safety checks.
8. Validate syntax and any existing relevant tests.

## Verification Requirements

Minimum:

```powershell
python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py
```

If a separate helper module is added, compile that file too.

Recommended non-live validation:

- Run prompt-only or other non-WeCom-safe mode only if it does not trigger live desktop automation.
- If practical, add or run a unit-level smoke check for the keep-awake helper on Windows.

Do not run supervised full-auto WeCom collection without current user authorization and supervision.

## Acceptance Criteria

- Supervised collection attempts to keep the display/system awake for the active run.
- The keep-awake request is released on success, failure, and interruption.
- Existing WeCom safety boundaries remain unchanged.
- Trace/log output makes the keep-awake state visible for diagnostics.
- No permanent power-plan, registry, screen saver, or lock-policy changes are made.
- The implementation is Windows-scoped and does not break non-Windows fallback/import behavior.

## Acceptance Round 1 (2026-07-06)

Result: rework required.

Validated:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `--prompt-only` remained non-live and did not trigger keep-awake or desktop automation.
- The change is scoped to `collect_wecom_smart_summary.py` and does not appear to alter OCR, copy, fingerprint, or page-safety state-machine logic.

Remaining issues:

1. `keep_awake()` is called from `main()` without passing the `TraceLogger`, while the trace is created inside `run_automation()`. As a result, keep-awake enable/disable/failure events are printed to console but are not written into the run's `trace.jsonl`, so the trace acceptance criterion is not met.
2. `SetThreadExecutionState` failure is not detected correctly. The Windows API returns `0` on failure and normally does not raise a Python exception. The current implementation sets `enabled = True` immediately after the call even if the return value is `0`, which can falsely report success and skip the intended `enable_failed` diagnostic path.

Rework scope:

- Only fix the two issues above.
- Do not expand feature scope.
- Do not change the WeCom collector state machine, OCR, copy strategy, wait-result logic, fingerprint verification, or foreground/page-state checks.
- Do not run full-auto live WeCom testing unless the user is supervising and explicitly authorizes it.

## Acceptance Round 2 (2026-07-06)

Result: accepted.

Validated:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --prompt-only --period '2026-07-01..2026-07-05'` passed and remained non-live.
- Mocked non-live automation failure path confirmed successful keep-awake enable writes `event="keep_awake", state="enabled"` to the current run trace and release writes `event="keep_awake", state="disabled"` after process exit cleanup.
- Mocked `SetThreadExecutionState` return value `0` path confirmed it writes `event="keep_awake", state="enable_failed"` and does not mark the guard enabled.

Acceptance notes:

- No live full-auto WeCom test was run.
- The implementation now satisfies the requested behavior for the CLI supervised automation path.
- Minor cleanup opportunity remains: the earlier `keep_awake()` context manager is now unused after the logic moved into `run_automation()`. This is non-blocking but can be removed in a future tidy pass.

## References

- Microsoft `SetThreadExecutionState`: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
- Microsoft system sleep criteria: https://learn.microsoft.com/en-us/windows/win32/power/system-sleep-criteria
- PowerToys Awake: https://learn.microsoft.com/en-us/windows/powertoys/awake
- wakepy project: https://github.com/fohrloop/wakepy
- py-setthreadexecutionstate example: https://github.com/darfink/py-setthreadexecutionstate
