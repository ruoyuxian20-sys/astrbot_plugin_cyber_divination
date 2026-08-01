"""奇门遁甲（简式时家排盘）：以节气近似定月建与阴阳遁，未处理超接置闰；九星八门八神按九宫序顺逆飞布，神盘不入中五；日干支以 1949-10-01（甲子日）为基准推算。"""
# 排盘输出长行为有意为之：
# ruff: noqa: E501
from __future__ import annotations

from datetime import date, datetime

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

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


def _stem_branch(index: int) -> str:
    return STEMS[index % 10] + BRANCHES[index % 12]


def _day_ganzhi_index(d: date) -> int:
    """日干支序号：1949-10-01 为甲子（0）。"""
    anchor = date(1949, 10, 1)
    return (d - anchor).days % 60


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
    year_pillar = _stem_branch(year)

    term = _current_term(dt)
    month_branch = term["month_branch"]
    # 五虎遁：年干 -> 寅月干
    wuhu_base = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0}
    month_stem = (wuhu_base[year % 5] + (month_branch - 2) % 12) % 10
    month_pillar = STEMS[month_stem] + BRANCHES[month_branch]

    day_index = _day_ganzhi_index(dt.date())
    day_pillar = _stem_branch(day_index)

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


def build_result(time_str: str = "", question: str = "", sender: str = "") -> str:
    """生成奇门遁甲排盘结果文本。time_str 形如 YYYY-MM-DD HH:MM 或 YYYY-MM-DD。"""
    dt = datetime.now()
    if time_str:
        try:
            clean = time_str.strip().replace("/", "-").replace("：", ":")
            if len(clean.split()) == 1:
                dt = datetime.strptime(clean, "%Y-%m-%d").replace(hour=12, minute=0)
            else:
                dt = datetime.strptime(clean, "%Y-%m-%d %H:%M")
        except ValueError:
            pass

    pan = make_pan(dt)
    year_p, month_p, day_p, hour_p = pan["pillars"]

    parts = ["🔮 奇门遁甲 · 简式时家排盘"]
    if question:
        parts.append(f"所问之事：{question}")
    if sender:
        parts.append(f"问卜人：{sender}")
    parts.append("")
    parts.append(f"求测时刻：{dt:%Y-%m-%d %H:%M}")
    parts.append(f"四柱：{year_p}年 {month_p}月 {day_p}日 {hour_p}时")
    parts.append(f"用局：{pan['phase']}{pan['ju']}局（{pan['yuan']}，{pan['term']}）")
    parts.append(f"值符：{pan['zhifu_star']}  值使：{pan['zhishi_door']}门")
    parts.append("")
    parts.append("九宫盘：")
    for palace in [4, 9, 2, 3, 5, 7, 8, 1, 6]:
        parts.append(_display_palace(pan, palace))
    parts.append("")
    parts.append("简断：")
    parts.append(f"· 值符{pan['zhifu_star']}落{_PALACE_NAMES[pan['shi_gan_palace']]}：{STAR_MEANINGS[pan['zhifu_star']]}")
    zhishi_display = pan["zhishi_palace"]
    if zhishi_display == 5:
        zhishi_display = 2
    parts.append(f"· 值使{pan['zhishi_door']}门落{_PALACE_NAMES[zhishi_display]}：{DOOR_MEANINGS[pan['zhishi_door']]}")
    zhifu_god = pan["shen_pan"].get(pan["shi_gan_palace"], "九天")
    parts.append(f"· 值符宫临{zhifu_god}神：{GOD_MEANINGS[zhifu_god]}")
    parts.append("")
    parts.append("※ 简式排盘未含超接置闰等细则，结果仅供娱乐参考。")
    return "\n".join(parts)
