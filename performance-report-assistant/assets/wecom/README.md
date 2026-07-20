# WeCom Template Assets

OpenCV template matching images for WeCom Smart Summary automation.

Templates must be captured from the target machine at the actual resolution/DPI used during
automation. Template file naming convention:

```
{control}_{resolution}_{theme}.png
```

Examples:
- `plus_1080p_light.png` — "+" new-summary button
- `start_summary_1080p_light.png` — "开始总结" button
- `copy_1080p_light.png` — "复制" button

## Important

- Do NOT fabricate template images. If no template file exists for a control,
  the automation will fall back to OCR and log a missing-template warning.
- To create templates: run `--probe-only` with an explicit absolute
  `--screenshot-dir`, inspect its `regions/` screenshots, crop the target
  control, and save it here with the appropriate name. Full-auto runs without
  an explicit diagnostics path use `%TEMP%\wecom_runs\<run-id>\`; failed runs
  retain that bundle, while successful runs clean it automatically.
