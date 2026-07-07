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
- To create templates: run `--probe-only`, inspect the region screenshots in
  the configured run diagnostics directory, such as
  `outputs/wecom_runs/<run-id>/regions/`, crop the target control, and save it
  here with the appropriate name.
