# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors

from typing import Dict


def _line(char: str = "-", width: int = 60) -> str:
    return char * width


def print_header(title: str) -> None:
    print()
    print(_line("="))
    print(title)
    print(_line("="))


def print_subheader(title: str) -> None:
    print()
    print(title)
    print(_line("-"))


def print_kv(label: str, value, indent: int = 0) -> None:
    prefix = " " * indent
    print(f"{prefix}{label}: {value}")


def print_list(items, indent: int = 2) -> None:
    prefix = " " * indent
    for entry in items:
        print(f"{prefix}- {entry}")


def print_matrix(title: str, matrix: Dict[str, Dict[str, float]], indent: int = 2) -> None:
    print_subheader(title)
    for row_key, cols in matrix.items():
        cells = [f"{col}={val:.2f}" for col, val in cols.items()]
        print_kv(row_key, ", ".join(cells), indent)
