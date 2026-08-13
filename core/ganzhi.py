"""干支基础工具：天干地支与日干支推算（纯 Python）。"""
from __future__ import annotations

from datetime import date

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def stem_branch(index: int) -> str:
    """由干支序号（0=甲子）返回干支字符串。"""
    return STEMS[index % 10] + BRANCHES[index % 12]


def day_ganzhi_index(d: date) -> int:
    """日干支序号：1949-10-01 为甲子（0）。"""
    anchor = date(1949, 10, 1)
    return (d - anchor).days % 60
