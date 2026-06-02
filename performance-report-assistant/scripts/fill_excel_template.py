#!/usr/bin/env python
"""Fill an Excel template copy while preserving workbook formatting."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def flatten_mapping(raw: dict[str, Any]) -> dict[tuple[str, str], Any]:
    flattened: dict[tuple[str, str], Any] = {}
    for key, value in raw.items():
        if "!" in key:
            sheet, cell = key.split("!", 1)
            flattened[(sheet, cell)] = value
        elif isinstance(value, dict):
            for cell, cell_value in value.items():
                flattened[(key, cell)] = cell_value
        else:
            raise ValueError(f"Invalid mapping entry: {key}")
    return flattened


def merged_anchor(ws: Any, cell_ref: str) -> str:
    from openpyxl.cell.cell import MergedCell

    cell = ws[cell_ref]
    if not isinstance(cell, MergedCell):
        return cell_ref

    for merged_range in ws.merged_cells.ranges:
        if cell.coordinate in merged_range:
            return merged_range.start_cell.coordinate
    return cell_ref


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill values into a copied .xlsx template.")
    parser.add_argument("--template", required=True, help="Original .xlsx template path.")
    parser.add_argument("--mapping", required=True, help="JSON mapping file.")
    parser.add_argument("--output", required=True, help="Output .xlsx path.")
    args = parser.parse_args()

    from openpyxl import load_workbook
    from openpyxl.styles import Alignment

    template = Path(args.template)
    mapping_path = Path(args.mapping)
    output = Path(args.output)

    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, output)

    mapping = flatten_mapping(json.loads(mapping_path.read_text(encoding="utf-8")))
    wb = load_workbook(output)

    for (sheet_name, cell_ref), value in mapping.items():
        if sheet_name not in wb.sheetnames:
            raise KeyError(f"Sheet not found: {sheet_name}")
        ws = wb[sheet_name]
        target_ref = merged_anchor(ws, cell_ref)
        cell = ws[target_ref]
        cell.value = value
        cell.alignment = Alignment(
            horizontal=cell.alignment.horizontal,
            vertical=cell.alignment.vertical,
            text_rotation=cell.alignment.text_rotation,
            wrap_text=True,
            shrink_to_fit=cell.alignment.shrink_to_fit,
            indent=cell.alignment.indent,
        )

    wb.save(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
