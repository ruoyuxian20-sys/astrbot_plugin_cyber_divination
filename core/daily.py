"""每日运势：按（日期, 用户）稳定抽取塔罗 + 灵签 + 周易的综合运势卡。"""
from __future__ import annotations

import hashlib
import random
from datetime import date

from . import lingqian, tarot, zhouyi
from .ganzhi import day_ganzhi_index

# 按灵签吉凶给出一句综合建议（确定性）
_GRADE_ADVICE = {
    "上上": "诸事顺遂，适合主动出击、把握良机。",
    "上签": "运势不错，按部就班推进，多有好消息。",
    "中签": "平稳中有小波折，宜稳扎稳打、量力而行。",
    "中平": "平常心对待，守成蓄力，静待时机。",
    "下签": "今日宜低调谨慎，少做重大决定，养精蓄锐。",
}


def daily_seed(d: date, uid: str) -> int:
    """稳定种子：同一（日期, 用户）结果固定，且跨进程一致。"""
    raw = f"{d.isoformat()}|{uid}".encode()
    return int.from_bytes(hashlib.md5(raw).digest()[:8], "big")


def draw_daily(d: date, uid: str) -> dict:
    """抽取当日运势数据：塔罗单张 + 灵签 + 周易卦象（含六神）。"""
    rng = random.Random(daily_seed(d, uid))
    card = tarot.draw_single(rng)
    number, grade, poem, explain = lingqian.draw(rng)
    cast = zhouyi.cast(rng=rng, day_index=day_ganzhi_index(d))
    return {
        "date": d,
        "card": card,
        "lingqian": (number, grade, poem, explain),
        "cast": cast,
    }


def format_daily(data: dict, uid_name: str = "") -> str:
    """把每日运势数据排版为文本。"""
    d: date = data["date"]
    name, is_reversed, meaning = data["card"]
    number, grade, poem, explain = data["lingqian"]
    cast: zhouyi.ZhouyiCast = data["cast"]

    parts = [f"🔮 每日运势 · {d:%Y-%m-%d}"]
    if uid_name:
        parts.append(f"求运人：{uid_name}")
    parts.append("")
    state = "逆位" if is_reversed else "正位"
    parts.append(f"塔罗指引：{name}（{state}）")
    parts.append(f"  → {meaning}")
    parts.append("")
    parts.append(f"灵签：第 {number} 签 · {grade}")
    parts.append(f"  签诗：{poem.replace(chr(10), ' ')}")
    parts.append(f"  → {explain}")
    parts.append("")
    parts.append(f"周易卦象：{zhouyi.hexagram_symbol(cast.number)} {cast.name}卦")
    parts.append(f"  → {cast.jie}")
    if cast.moving and cast.changed_number is not None:
        dyn = "、".join(str(i) for i in cast.moving)
        parts.append(f"  动爻第{dyn}爻，变{cast.changed_name}卦，事有变化之机")
    parts.append("")
    parts.append(f"综合建议：{_GRADE_ADVICE.get(grade, '顺其自然，过好当下。')}")
    parts.append("")
    parts.append("※ 每日运势当天固定、明日刷新；仅供娱乐参考。")
    return "\n".join(parts)


def build_result(d: date | None = None, uid: str = "", uid_name: str = "") -> str:
    """生成每日运势文本（默认取今天）。"""
    d = d or date.today()
    return format_daily(draw_daily(d, uid), uid_name)
