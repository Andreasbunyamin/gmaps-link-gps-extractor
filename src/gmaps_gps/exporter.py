"""Write a DataFrame to a readable, pre-formatted Excel sheet."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

__all__ = ["save_formatted_excel"]

DEFAULT_FONT = "Calibri"
DEFAULT_FONT_SIZE = 11
HEADER_FILL = "#FFE699"
COLUMN_PADDING = 5
MAX_COLUMN_WIDTH = 60


def save_formatted_excel(
    df: pd.DataFrame,
    path: str | Path,
    sheet_name: str = "Sheet1",
    font_name: str = DEFAULT_FONT,
    font_size: int = DEFAULT_FONT_SIZE,
    header_fill: str = HEADER_FILL,
) -> Path:
    """Save ``df`` with a highlighted header row and auto-fitted columns.

    Args:
        df: The table to write.
        path: Destination ``.xlsx`` file. Parent folders are created.
        sheet_name: Worksheet name.
        font_name: Font applied to header and body.
        font_size: Point size applied to header and body.
        header_fill: Hex colour for the header background.

    Returns:
        The path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        workbook = writer.book

        header_format = workbook.add_format({
            "bold": True,
            "fg_color": header_fill,
            "border": 0,
            "align": "center",
            "valign": "vcenter",
            "font_name": font_name,
            "font_size": font_size,
        })
        body_format = workbook.add_format({
            "border": 0,
            "align": "center",
            "valign": "vcenter",
            "font_name": font_name,
            "font_size": font_size,
        })

        # Write the body one row down, then lay the styled header over row 0.
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
        worksheet = writer.sheets[sheet_name]

        for index, column in enumerate(df.columns):
            longest_cell = df[column].astype(str).str.len().max()
            width = min(max(int(longest_cell or 0), len(str(column))) + COLUMN_PADDING,
                        MAX_COLUMN_WIDTH)
            worksheet.set_column(index, index, width, body_format)
            worksheet.write(0, index, column, header_format)

        worksheet.freeze_panes(1, 0)

    return path
