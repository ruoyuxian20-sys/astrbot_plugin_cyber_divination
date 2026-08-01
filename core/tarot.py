"""塔罗牌：大阿卡纳 22 张 + 小阿卡纳 56 张，正位/逆位释义。"""
# 牌义长行为有意为之：
# ruff: noqa: E501
from __future__ import annotations

import random

# (牌名, 正位含义, 逆位含义)
MAJOR_ARCANA: list[tuple[str, str, str]] = [
    ("0 愚者 The Fool", "新的开始、自由、冒险精神", "鲁莽冲动、犹豫不决、逃避现实"),
    ("I 魔术师 The Magician", "创造、技能、意志力、行动力", "欺骗操纵、才能浪费、方向混乱"),
    ("II 女祭司 The High Priestess", "直觉、潜意识、神秘智慧", "忽视直觉、浮于表面、信息缺失"),
    ("III 皇后 The Empress", "丰饶、母性、滋养、创造", "过度付出、依赖他人、创造力受阻"),
    ("IV 皇帝 The Emperor", "权威、秩序、稳定、掌控", "专制固执、控制欲强、僵化"),
    ("V 教皇 The Hierophant", "传统、信仰、教导、指引", "教条束缚、墨守成规、反叛"),
    ("VI 恋人 The Lovers", "爱情、和谐、选择、共鸣", "分歧冲突、价值观矛盾、犹豫"),
    ("VII 战车 The Chariot", "胜利、意志力、进取、掌控方向", "失控、方向迷失、受阻停滞"),
    ("VIII 力量 Strength", "勇气、耐心、内在力量、温柔", "软弱、自我怀疑、冲动失控"),
    ("IX 隐士 The Hermit", "内省、独处、寻求真理、智慧", "孤立逃避、过度封闭、拒绝帮助"),
    ("X 命运之轮 Wheel of Fortune", "转折、机遇、命运流转", "厄运、失控、低谷周期"),
    ("XI 正义 Justice", "公正、因果、真相、平衡", "不公、偏见、逃避责任"),
    ("XII 倒吊人 The Hanged Man", "牺牲、换位思考、暂停、觉悟", "拖延、无谓牺牲、僵局"),
    ("XIII 死神 Death", "结束、蜕变、放下、新生", "抗拒改变、停滞、恐惧失去"),
    ("XIV 节制 Temperance", "平衡、调和、耐心、适度", "失衡、极端、急躁冒进"),
    ("XV 恶魔 The Devil", "欲望、束缚、诱惑、执念", "挣脱束缚、觉醒、戒除恶习"),
    ("XVI 高塔 The Tower", "突变、崩塌、真相爆发", "避免灾难、延迟的变动、恐惧"),
    ("XVII 星星 The Star", "希望、疗愈、灵感、宁静", "失望、失去信心、方向模糊"),
    ("XVIII 月亮 The Moon", "潜意识、幻象、不安、直觉", "拨云见日、澄清疑虑、释然"),
    ("XIX 太阳 The Sun", "成功、活力、光明、喜悦", "暂时阴霾、过度乐观、小挫"),
    ("XX 审判 Judgement", "觉醒、重生、召唤、释怀", "自我怀疑、错过时机、悔恨"),
    ("XXI 世界 The World", "圆满、完成、成就、整合", "未完成、拖延、缺乏闭环"),
]

# 小阿卡纳：四组（权杖/圣杯/宝剑/星币），每组 14 张（王牌-10 + 侍从/骑士/王后/国王）
_MINOR_RANKS = ["王牌", "二", "三", "四", "五", "六", "七", "八", "九", "十", "侍从", "骑士", "王后", "国王"]

# (正位含义, 逆位含义)，顺序对应 _MINOR_RANKS
MINOR_ARCANA: dict[str, list[tuple[str, str]]] = {
    "权杖 Wands": [
        ("灵感的火花，新的行动开端", "热情难以持续，计划草率"),
        ("规划与决策，掌握主动权", "犹豫不决，计划生变"),
        ("远见与扩张，稳中求进", "阻力延迟，目光短浅"),
        ("庆祝与稳定，小有成就", "不安于现状，懈怠松懈"),
        ("竞争与冲突，需坦诚沟通", "和解有望，矛盾渐消"),
        ("胜利与认可，收获赞美", "骄傲自满，功亏一篑"),
        ("坚持立场，勇敢守卫", "疲于防守，力不从心"),
        ("快速进展，行动迅捷", "忙乱失控，节奏过快"),
        ("坚韧防守，坚守阵地", "疲惫多疑，过度防御"),
        ("负重前行，压力沉重", "卸下重担，轻装前进"),
        ("热情探索，充满好奇心", "三分钟热度，方向不定"),
        ("勇往直前，充满冲劲", "鲁莽冲动，不顾后果"),
        ("自信热忱，感染力强", "占有欲强，锋芒太露"),
        ("领导开创，魄力十足", "固执专断，听不进劝"),
    ],
    "圣杯 Cups": [
        ("情感的丰盈，新的感受", "情感空虚，爱的匮乏"),
        ("甜蜜的连结，两情相悦", "关系失衡，沟通疏离"),
        ("友谊与庆祝，群聚之乐", "过度放纵，表面热闹"),
        ("倦怠与不满足，寻求更多", "重拾热情，不再麻木"),
        ("失落与遗憾，放下执念", "接受现实，走出阴霾"),
        ("回忆与纯真，旧友重逢", "沉溺过去，无法前进"),
        ("幻想与选择，想象丰富", "清醒务实，不再做梦"),
        ("离开舒适区，寻找真义", "害怕改变，裹足不前"),
        ("愿望成真，心满意足", "得意忘形，乐极生悲"),
        ("家庭圆满，情感富足", "情感破裂，家庭失和"),
        ("感性的消息，情感萌芽", "情绪幼稚，轻信他人"),
        ("浪漫的追求，心动时刻", "不切实际，空想过度"),
        ("温柔共情，善解人意", "情绪泛滥，界限模糊"),
        ("情感成熟，包容稳定", "情感压抑，故作坚强"),
    ],
    "宝剑 Swords": [
        ("真相洞见，思想清晰", "混乱误解，判断失误"),
        ("权衡利弊，僵持对峙", "打破僵局，做出抉择"),
        ("心碎伤痛，言语伤人", "伤口愈合，释怀原谅"),
        ("休整静养，暂避纷争", "恢复行动，重新出发"),
        ("惨胜纷争，得不偿失", "和解放下，另寻出路"),
        ("过渡与转机，逐渐好转", "困境滞留，焦虑未消"),
        ("策略与隐瞒，暗度陈仓", "坦白面对，真相大白"),
        ("自我束缚，思维设限", "挣脱枷锁，解放自己"),
        ("焦虑噩梦，忧思过度", "放下担忧，找回平静"),
        ("谷底终结，触底反弹", "否极泰来，重获新生"),
        ("警觉好奇，观察敏锐", "言语轻率，口无遮拦"),
        ("果断冲刺，雷厉风行", "鲁莽攻击，不计后果"),
        ("冷静理性，洞察人心", "冷漠尖刻，过于理性"),
        ("睿智公正，思虑周全", "滥用权谋，偏见武断"),
    ],
    "星币 Pentacles": [
        ("财富机遇，新的起点", "错失良机，财务不稳"),
        ("平衡调度，灵活周转", "顾此失彼，开支失衡"),
        ("合作精进，团队协作", "质量粗糙，配合不佳"),
        ("稳固积蓄，安于现状", "吝啬守旧，不敢投入"),
        ("匮乏困境，暂时拮据", "迎来转机，困境将解"),
        ("施与受的平衡，慷慨分享", "吝啬失衡，付出不均"),
        ("耐心耕耘，等待收获", "急于求成，进度放缓"),
        ("勤勉精进，熟能生巧", "重复枯燥，机械应付"),
        ("独立富足，自得其乐", "孤芳自赏，与世隔绝"),
        ("家族昌盛，基业稳固", "物质至上，忽视情感"),
        ("学习实践，积累经验", "三心二意，半途而废"),
        ("踏实稳健，一步一个脚印", "停滞不前，缺乏动力"),
        ("务实滋养，照顾周全", "过度操劳，忘记自己"),
        ("事业有成，理财有道", "固执守财，不懂变通"),
    ],
}


def _all_cards() -> list[tuple[str, str, str]]:
    cards = [("大阿卡纳 " + name, upright, reversed_) for name, upright, reversed_ in MAJOR_ARCANA]
    for suit, entries in MINOR_ARCANA.items():
        for rank, (upright, reversed_) in zip(_MINOR_RANKS, entries, strict=True):
            cards.append((f"{suit.split()[0]}{rank}", upright, reversed_))
    return cards


ALL_CARDS = _all_cards()


def draw_single(rng: random.Random | None = None) -> tuple[str, bool, str]:
    """抽一张牌：返回 (牌名, 是否逆位, 释义)。"""
    rng = rng or random.SystemRandom()
    name, upright, reversed_ = ALL_CARDS[rng.randrange(len(ALL_CARDS))]
    is_reversed = rng.random() < 0.5
    return name, is_reversed, (reversed_ if is_reversed else upright)


def draw_three(rng: random.Random | None = None) -> list[tuple[str, str, bool, str]]:
    """三张牌阵（过去/现在/未来）：[(位置, 牌名, 是否逆位, 释义)]。"""
    rng = rng or random.SystemRandom()
    positions = ["过去", "现在", "未来"]
    result = []
    for pos in positions:
        name, is_reversed, meaning = draw_single(rng)
        result.append((pos, name, is_reversed, meaning))
    return result


def build_result(spread: str = "single", question: str = "", sender: str = "") -> str:
    """生成塔罗占卜结果文本。spread: single / three。"""
    parts = ["🔮 塔罗牌占卜"]
    if question:
        parts.append(f"所问之事：{question}")
    if sender:
        parts.append(f"问卜人：{sender}")
    parts.append("")

    if spread == "three":
        parts.append("牌阵：过去 · 现在 · 未来")
        parts.append("")
        for pos, name, is_reversed, meaning in draw_three():
            state = "逆位" if is_reversed else "正位"
            parts.append(f"【{pos}】{name}（{state}）")
            parts.append(f"  → {meaning}")
            parts.append("")
    else:
        parts.append("牌阵：单张指引")
        parts.append("")
        name, is_reversed, meaning = draw_single()
        state = "逆位" if is_reversed else "正位"
        parts.append(f"【今日指引】{name}（{state}）")
        parts.append(f"  → {meaning}")
        parts.append("")

    parts.append("※ 塔罗占卜仅供参考娱乐，请理性看待。")
    return "\n".join(parts)
