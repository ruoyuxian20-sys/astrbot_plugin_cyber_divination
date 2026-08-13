"""奇门遁甲（简式时家排盘）：以节气近似定月建与阴阳遁，未处理超接置闰；九星八门八神按九宫序顺逆飞布，神盘不入中五；日干支以 1949-10-01（甲子日）为基准推算。"""
# 排盘输出长行为有意为之。
from __future__ import annotations

import re
from datetime import datetime

from .ganzhi import BRANCHES, STEMS, day_ganzhi_index, stem_branch

# 二十四节气（近似日期）：(月, 日, 名称, 月支序号, 阴阳遁)
TERMS = [
    (12, 7, "大雪", 0, "yin"),
    (12, 22, "冬至", 0, "yang"),
    (1, 6, "小寒", 1, "yang"),
    (1, 21, "大寒", 2, "yang"),
    (2, 4, "立春", 3, "yang"),
    (2, 19, "雨水", 4, "yang"),
    (3, 6, "惊蛰", 5, "yang"),
    (3, 21, "春分", 6, "yang"),
    (4, 5, "清明", 7, "yang"),
    (4, 20, "谷雨", 8, "yang"),
    (5, 6, "立夏", 9, "yang"),
    (5, 21, "小满", 10, "yang"),
    (6, 6, "芒种", 11, "yang"),
    (6, 22, "夏至", 0, "yin"),
    (7, 7, "小暑", 1, "yin"),
    (7, 23, "大暑", 2, "yin"),
    (8, 8, "立秋", 3, "yin"),
    (8, 23, "处暑", 4, "yin"),
    (9, 8, "白露", 5, "yin"),
    (9, 23, "秋分", 6, "yin"),
    (10, 8, "寒露", 7, "yin"),
    (10, 23, "霜降", 8, "yin"),
    (11, 7, "立冬", 9, "yin"),
    (11, 22, "小雪", 10, "yin"),
]

# 三元局数表（上元/中元/下元）
YANG_JU = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (4, 1, 7), "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
}
YIN_JU = {
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "处暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (6, 9, 3), "霜降": (5, 8, 2),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}

_PALACE_NAMES = {
    1: "坎一", 2: "坤二", 3: "震三", 4: "巽四", 5: "中五",
    6: "乾六", 7: "兑七", 8: "艮八", 9: "离九",
}
_STARS = {1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅", 5: "天禽", 6: "天心", 7: "天柱", 8: "天任", 9: "天英"}
_DOORS = {1: "休", 2: "死", 3: "伤", 4: "杜", 5: "死", 6: "开", 7: "惊", 8: "生", 9: "景"}
_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
_INSTRUMENTS = "戊己庚辛壬癸丁丙乙"

STAR_MEANINGS = {
    "天蓬": "智谋胆识，主暗昧谋略，宜深谋远虑。",
    "天芮": "柔韧包容，主疾病晦滞，宜调养身心。",
    "天冲": "威猛果决，主振作行动，宜勇往直前。",
    "天辅": "文教辅佐，主文昌和顺，宜学习求教。",
    "天禽": "中正无私，主守成平稳，宜脚踏实地。",
    "天心": "机敏谋划，主医药仁善，宜未雨绸缪。",
    "天柱": "刚直口利，主口舌抗争，宜谨言慎行。",
    "天任": "任劳任怨，主厚道守信，宜守业固本。",
    "天英": "光明声名，主急躁虚华，宜沉心静气。",
}
DOOR_MEANINGS = {
    "休": "休养生息，贵人相助，为吉门。",
    "生": "生机财利，顺遂如意，为吉门。",
    "伤": "伤损竞争，宜防冲突，为凶门。",
    "杜": "闭塞不通，行动迟滞，宜守不宜攻。",
    "景": "文书虚华，利考试展示，余事多虚。",
    "死": "死寂无用，诸事不利，宜静不宜动。",
    "惊": "惊恐口舌，防是非惊扰，为凶门。",
    "开": "开张顺利，诸事可成，为大吉门。",
}
GOD_MEANINGS = {
    "值符": "贵人庇护，正统得力。",
    "螣蛇": "虚惊怪异，防不实之事。",
    "太阴": "暗中相助，宜隐忍策划。",
    "六合": "合作姻缘，和合之事。",
    "白虎": "凶险阻隔，宜防血光口舌。",
    "玄武": "盗贼欺瞒，防小人暗算。",
    "九地": "稳固低伏，宜守成蓄势。",
    "九天": "高远进取，利于远行谋大。",
}

_NOW_TOKENS = {"现在", "now", "此刻", "当前"}
# 起局时间：2026-08-01 15:30 / 2026-8-1 / 2026年8月1日 15:30 等
_TIME_RE = re.compile(
    r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?(?:\s+\d{1,2}[:：]\d{2})?"
)


def _normalize_time_str(time_str: str) -> str:
    """归一化时间字符串：/→-、全角冒号→半角、中文年月日→分隔符、压缩空白。"""
    clean = time_str.strip().replace("/", "-").replace("：", ":")
    clean = re.sub(r"\s*年\s*", "-", clean)
    clean = re.sub(r"\s*月\s*", "-", clean)
    clean = re.sub(r"\s*日\s*", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()


def parse_time(time_str: str) -> datetime | None:
    """解析起局时间：YYYY-MM-DD [HH:MM]（支持中文日期与全角冒号）。

    空串、「现在」等关键词或解析失败返回 None（调用方按当前时刻起局）。
    """
    if not time_str:
        return None
    clean = _normalize_time_str(time_str)
    if clean.lower() in _NOW_TOKENS:
        return None
    try:
        if len(clean.split()) == 1:
            return datetime.strptime(clean, "%Y-%m-%d").replace(hour=12, minute=0)
        return datetime.strptime(clean, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def is_date_only(time_str: str) -> bool:
    """判断时间串是否只含日期（无时刻部分）。"""
    if not time_str:
        return False
    clean = _normalize_time_str(time_str)
    return bool(clean) and len(clean.split()) == 1


def split_time_question(text: str) -> tuple[str, str]:
    """从文本中提取起局时间与所问之事；支持「现在」等关键词表示自动取当前时刻。"""
    match = _TIME_RE.search(text)
    if match:
        time_str = match.group(0)
        question = re.sub(
            r"\s+", " ", f"{text[: match.start()]} {text[match.end():]}"
        ).strip()
        return time_str, question
    tokens = text.split(maxsplit=1)
    if tokens and tokens[0].strip("，,。.").lower() in _NOW_TOKENS:
        return "", (tokens[1].strip() if len(tokens) > 1 else "")
    return "", text


def _current_term(dt: datetime) -> dict:
    """返回当前所处的节气（含阴阳遁与月支）。"""
    key = (dt.month, dt.day)
    matched = None
    for term in TERMS:
        if (term[0], term[1]) <= key:
            matched = term
    if matched is None:
        matched = (12, 7, "大雪", 0, "yin")
    return {
        "name": matched[2],
        "month_branch": matched[3],
        "phase": matched[4],
    }


def get_four_pillars(dt: datetime) -> tuple[str, str, str, str, int]:
    """返回 (年柱, 月柱, 日柱, 时柱, 日干支序号)。"""
    # 年柱以立春（约 2/4）为界换年
    if (dt.month, dt.day) < (2, 4):
        year = (dt.year - 5) % 60
    else:
        year = (dt.year - 4) % 60
    year_pillar = stem_branch(year)

    term = _current_term(dt)
    month_branch = term["month_branch"]
    # 五虎遁：年干 -> 寅月干
    wuhu_base = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0}
    month_stem = (wuhu_base[year % 5] + (month_branch - 2) % 12) % 10
    month_pillar = STEMS[month_stem] + BRANCHES[month_branch]

    day_index = day_ganzhi_index(dt.date())
    day_pillar = stem_branch(day_index)

    hour_branch = ((dt.hour + 1) // 2) % 12
    # 五鼠遁：日干 -> 子时干
    wushu_base = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}
    hour_stem = (wushu_base[day_index % 5] + hour_branch) % 10
    hour_pillar = STEMS[hour_stem] + BRANCHES[hour_branch]
    return year_pillar, month_pillar, day_pillar, hour_pillar, day_index


def make_pan(dt: datetime) -> dict:
    """起局，返回排盘结果字典。"""
    year_pillar, month_pillar, day_pillar, hour_pillar, day_index = get_four_pillars(dt)
    term = _current_term(dt)
    is_yang = term["phase"] == "yang"

    day_branch = day_index % 12
    if day_branch in (0, 6, 3, 9):
        yuan, yuan_idx = "上元", 0
    elif day_branch in (2, 8, 5, 11):
        yuan, yuan_idx = "中元", 1
    else:
        yuan, yuan_idx = "下元", 2

    ju_table = YANG_JU if is_yang else YIN_JU
    ju = ju_table[term["name"]][yuan_idx]

    palace_seq = list(range(1, 10)) if is_yang else list(range(9, 0, -1))
    # 地盘布三奇六仪
    di_pan: dict[str, int] = {}
    for i, ins in enumerate(_INSTRUMENTS):
        di_pan[ins] = palace_seq[(ju - 1 + i) % 9]

    # 时干支序号与旬首
    hour_index = next(
        t for t in range(60)
        if STEMS[t % 10] == hour_pillar[0] and BRANCHES[t % 12] == hour_pillar[1]
    )
    xun = hour_index // 10
    xun_yi = "戊己庚辛壬癸"[xun]
    xun_branch = (xun * 10) % 12
    xun_palace = di_pan[xun_yi]

    # 时干落宫
    shi_gan = hour_pillar[0]
    if shi_gan in "甲乙":
        shi_gan_palace = xun_palace
    else:
        shi_gan_palace = di_pan[shi_gan]

    # 天盘九星：值符星随“时干”转动
    delta = (palace_seq.index(shi_gan_palace) - palace_seq.index(xun_palace)) % 9
    tian_pan: dict[int, str] = {}
    for palace, star in _STARS.items():
        tian_pan[palace_seq[(palace_seq.index(palace) + delta) % 9]] = star

    zhifu_star = _STARS[xun_palace]
    zhishi_door = _DOORS[xun_palace]

    # 八门：值使门从旬首宫顺/逆行走（12 时辰一循环，取 %9）
    steps = (hour_index % 12 - xun_branch) % 12
    move = steps % 9
    zhishi_palace = palace_seq[
        (palace_seq.index(xun_palace) + (move if is_yang else -move)) % 9
    ]
    door_order = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
    door_seq = [p for p in palace_seq if p != 5]
    start_door = door_seq.index(zhishi_palace) if zhishi_palace in door_seq else door_seq.index(2)
    men_pan: dict[int, str] = {}
    for i, door in enumerate(door_order):
        men_pan[door_seq[(start_door + i) % 8]] = door
    men_pan[5] = "死"

    # 八神：值符随值符星落宫，神不入中五
    god_seq = [p for p in palace_seq if p != 5]
    god_start_palace = shi_gan_palace if shi_gan_palace in god_seq else 2
    start_god = god_seq.index(god_start_palace)
    shen_pan: dict[int, str] = {}
    for i, god in enumerate(_GODS):
        shen_pan[god_seq[(start_god + i) % 8]] = god

    return {
        "dt": dt,
        "pillars": (year_pillar, month_pillar, day_pillar, hour_pillar),
        "term": term["name"],
        "phase": "阳遁" if is_yang else "阴遁",
        "yuan": yuan,
        "ju": ju,
        "di_pan": di_pan,
        "tian_pan": tian_pan,
        "men_pan": men_pan,
        "shen_pan": shen_pan,
        "xun_palace": xun_palace,
        "shi_gan_palace": shi_gan_palace,
        "zhifu_star": zhifu_star,
        "zhishi_door": zhishi_door,
        "zhishi_palace": zhishi_palace,
    }


def _display_palace(pan: dict, palace: int) -> str:
    star = pan["tian_pan"][palace]
    door = pan["men_pan"][palace]
    god = pan["shen_pan"].get(palace, "-")
    instrument = next(ins for ins, p in pan["di_pan"].items() if p == palace)
    extra = "（寄坤二）" if palace == 5 else ""
    return f"{_PALACE_NAMES[palace]}宫{extra}：{star}/{door}门/{god}（{instrument}）"


def _palace_display(palace: int) -> str:
    """宫名显示：中五按「中五（寄坤二）」处理。"""
    return "中五（寄坤二）" if palace == 5 else _PALACE_NAMES[palace]


def summarize(pan: dict) -> str:
    """一行摘要（占卜历史用）。"""
    return f"{pan['phase']}{pan['ju']}局 · 值符{pan['zhifu_star']} · {pan['zhishi_door']}门"


def format_pan(pan: dict, question: str = "", sender: str = "", note: str = "") -> str:
    """把排盘结果排版为文本。note 为求测时刻的补充说明（自动检测/正午起局等）。"""
    dt: datetime = pan["dt"]
    year_p, month_p, day_p, hour_p = pan["pillars"]

    parts = ["🔮 奇门遁甲 · 简式时家排盘"]
    if question:
        parts.append(f"所问之事：{question}")
    if sender:
        parts.append(f"问卜人：{sender}")
    parts.append("")
    parts.append(f"求测时刻：{dt:%Y-%m-%d %H:%M}")
    if note:
        parts.append(note)
    parts.append(f"四柱：{year_p}年 {month_p}月 {day_p}日 {hour_p}时")
    parts.append(f"用局：{pan['phase']}{pan['ju']}局（{pan['yuan']}，{pan['term']}）")
    parts.append(f"值符：{pan['zhifu_star']}  值使：{pan['zhishi_door']}门")
    parts.append("")
    parts.append("九宫盘：")
    for palace in [4, 9, 2, 3, 5, 7, 8, 1, 6]:
        parts.append(_display_palace(pan, palace))
    parts.append("")
    parts.append("简断：")
    zhifu_palace = pan["shi_gan_palace"]
    parts.append(
        f"· 值符{pan['zhifu_star']}落{_palace_display(zhifu_palace)}："
        f"{STAR_MEANINGS[pan['zhifu_star']]}"
    )
    zhishi_display = 2 if pan["zhishi_palace"] == 5 else pan["zhishi_palace"]
    parts.append(
        f"· 值使{pan['zhishi_door']}门落{_PALACE_NAMES[zhishi_display]}："
        f"{DOOR_MEANINGS[pan['zhishi_door']]}"
    )
    god_palace = 2 if zhifu_palace == 5 else zhifu_palace
    zhifu_god = pan["shen_pan"].get(god_palace, "九天")
    parts.append(f"· 值符宫临{zhifu_god}神：{GOD_MEANINGS[zhifu_god]}")
    parts.append("")
    parts.append("※ 简式排盘未含超接置闰等细则，结果仅供娱乐参考。")
    return "\n".join(parts)


def build_result(time_str: str = "", question: str = "", sender: str = "") -> str:
    """生成奇门遁甲排盘结果文本（兼容包装）。

    time_str 形如 YYYY-MM-DD [HH:MM]（支持中文日期）；空串或解析失败按当前时刻起局，
    并附带相应提示。
    """
    provided = bool(time_str.strip())
    parsed = parse_time(time_str)
    dt = parsed or datetime.now()
    if parsed is None and provided:
        note = "⚠ 时间格式无法识别，已按当前时刻起局。"
    elif not provided:
        note = "（自动检测当前时刻起局）"
    elif is_date_only(time_str):
        note = "（仅提供日期，按当日正午起局）"
    else:
        note = ""
    return format_pan(make_pan(dt), question, sender, note=note)
