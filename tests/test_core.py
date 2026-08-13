"""核心逻辑测试：不依赖 AstrBot 运行时。"""
import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from cyber_divination.core import daily, ganzhi, lingqian, qimen, render, tarot, zhouyi


def test_hexagram_grid_complete():
    numbers = set()
    for row in zhouyi.HEX_GRID.values():
        numbers.update(row.values())
    assert numbers == set(range(1, 65))


def test_all_hexagram_entries():
    assert len(zhouyi.HEXAGRAMS) == 64
    for n in range(1, 65):
        name, guaci, jie = zhouyi.HEXAGRAMS[n]
        assert name and guaci and jie


def test_toss_and_resolve():
    rng = random.Random(42)
    for _ in range(50):
        lines = zhouyi.toss_hexagram(rng)
        assert len(lines) == 6
        assert all(v in (6, 7, 8, 9) for v in lines)
        num, upper, lower = zhouyi.resolve_hexagram(lines)
        assert 1 <= num <= 64
        assert upper in zhouyi.TRIGRAM_SYMBOLS
        assert lower in zhouyi.TRIGRAM_SYMBOLS


def test_changed_hexagram():
    lines = [9, 7, 8, 6, 7, 8]
    num, new = zhouyi.changed_hexagram(lines)
    assert new[0] == 6 and new[3] == 9
    assert 1 <= num <= 64


def test_zhouyi_build_result():
    text = zhouyi.build_result("明天出行", "测试")
    assert "六爻" in text and "卦辞" in text


def test_zhouyi_six_gods():
    assert zhouyi.six_gods(0) == ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
    assert zhouyi.six_gods(2)[0] == "朱雀"   # 丙日起朱雀
    assert zhouyi.six_gods(4)[0] == "勾陈"   # 戊日起勾陈
    assert zhouyi.six_gods(5)[0] == "螣蛇"   # 己日起螣蛇
    assert zhouyi.six_gods(6)[0] == "白虎"   # 庚日起白虎
    assert zhouyi.six_gods(8)[0] == "玄武"   # 壬日起玄武


def test_zhouyi_cast_and_summarize():
    cast = zhouyi.cast(rng=random.Random(42), day_index=0)
    assert cast.gods == zhouyi.six_gods(0)
    text = zhouyi.format_cast(cast, "出行", "测试")
    assert "六爻" in text and "青龙" in text
    summary = zhouyi.summarize(cast)
    assert summary.endswith("卦")
    assert "变" not in summary or "变" in text


def test_lingqian_complete():
    assert len(lingqian.LINGQIAN) == 100
    for _num, (grade, poem, explain) in enumerate(lingqian.LINGQIAN, 1):
        assert grade in ("上上", "上签", "中签", "中平", "下签")
        assert 1 <= poem.count("\n") <= 3
        assert explain


def test_lingqian_draw():
    rng = random.Random(7)
    num, _grade, _poem, _explain = lingqian.draw(rng)
    assert 1 <= num <= 100
    text = lingqian.build_result("考试", "小明")
    assert "签 ·" in text and "签诗" in text and "解曰" in text


def test_lingqian_format_draw():
    text = lingqian.format_draw(
        8, "上签",
        "云开月出见光明，万事从今渐渐成；\n若问前程何处是，青云直上步天庭。",
        "否极泰来，渐入佳境，前程光明。",
        "事业", "小明",
    )
    assert "第 8 签" in text and "小明" in text and "上签" in text


def test_tarot_counts():
    assert len(tarot.MAJOR_ARCANA) == 22
    assert sum(len(v) for v in tarot.MINOR_ARCANA.values()) == 56
    assert all(len(v) == 14 for v in tarot.MINOR_ARCANA.values())
    assert len(tarot.ALL_CARDS) == 78


def test_tarot_draw():
    rng = random.Random(1)
    name, _rev, meaning = tarot.draw_single(rng)
    assert name and meaning
    spread = tarot.draw_three(rng)
    assert len(spread) == 3
    text = tarot.build_result("three", "感情")
    assert "过去" in text and "未来" in text
    single = tarot.build_result("single")
    assert "单张指引" in single


def test_tarot_parse_spread():
    assert tarot.parse_spread("三张 感情") == ("three", "感情")
    assert tarot.parse_spread("三张牌 事业") == ("three", "事业")
    assert tarot.parse_spread("3张 学业") == ("three", "学业")
    assert tarot.parse_spread("3 财运") == ("three", "财运")
    assert tarot.parse_spread("three cards") == ("three", "cards")
    assert tarot.parse_spread("单张 爱情") == ("single", "爱情")
    assert tarot.parse_spread("一张 工作") == ("single", "工作")
    assert tarot.parse_spread("single") == ("single", "")
    assert tarot.parse_spread("明天运势如何") == ("single", "明天运势如何")
    assert tarot.parse_spread("") == ("single", "")


def test_tarot_three_unique():
    rng = random.Random(5)
    spread = tarot.draw_three(rng)
    names = [name for _pos, name, _rev, _meaning in spread]
    assert len(names) == len(set(names)) == 3


def test_tarot_format():
    rng = random.Random(2)
    cards = tarot.draw_three(rng)
    text = tarot.format_three(cards, "感情", "测试")
    assert "过去" in text and "未来" in text and "测试" in text
    name, is_reversed, meaning = tarot.draw_single(rng)
    single = tarot.format_single(name, is_reversed, meaning, "事业")
    assert "单张指引" in single and "事业" in single


def test_tarot_search():
    hits = tarot.search_cards("star")
    assert hits and any("星星" in name for name, _u, _r in hits)
    hits2 = tarot.search_cards("权杖二")
    assert hits2 and hits2[0][0] == "权杖二"
    assert tarot.search_cards("不存在的牌") == []
    assert tarot.search_cards("") == []


def test_ganzhi_known_dates():
    assert ganzhi.day_ganzhi_index(date(1949, 10, 1)) == 0
    assert ganzhi.day_ganzhi_index(date(2000, 1, 1)) == 54  # 戊午日
    assert ganzhi.stem_branch(54) == "戊午"


def test_qimen_four_pillars_known_date():
    dt = datetime(2000, 1, 1, 12, 0)
    year, month, day, hour, idx = qimen.get_four_pillars(dt)
    assert year == "己卯"  # 立春前仍属己卯年
    assert month == "丙子"  # 大雪(子月)至小寒前
    assert day == "戊午"  # 2000-01-01 为戊午日
    assert hour == "戊午"  # 戊日子时起壬子，午时为戊午
    assert idx % 10 == 4  # 日干为戊


def test_qimen_pan_invariants():
    pan = qimen.make_pan(datetime(2026, 8, 1, 15, 30))
    assert sorted(pan["di_pan"].values()) == list(range(1, 10))
    assert sorted(pan["tian_pan"]) == list(range(1, 10))
    assert sorted(pan["men_pan"]) == list(range(1, 10))
    assert len(pan["shen_pan"]) == 8
    assert pan["tian_pan"][pan["shi_gan_palace"]] == pan["zhifu_star"]
    text = qimen.build_result("2026-08-01 15:30", "出行", "测试")
    assert ("阴遁" in text or "阳遁" in text) and "九宫盘" in text


def test_qimen_random_smoke():
    rng = random.Random(3)
    base = datetime(2024, 1, 15, 12, 0)
    for _ in range(30):
        d = base + timedelta(days=rng.randrange(0, 700), hours=rng.randrange(0, 23))
        pan = qimen.make_pan(d)
        assert sorted(pan["tian_pan"]) == list(range(1, 10))
        assert sorted(pan["men_pan"]) == list(range(1, 10))
        assert pan["tian_pan"][pan["shi_gan_palace"]] == pan["zhifu_star"]


def test_qimen_parse_time():
    assert qimen.parse_time("2026-08-01 15:30") == datetime(2026, 8, 1, 15, 30)
    assert qimen.parse_time("2026/8/1") == datetime(2026, 8, 1, 12, 0)
    assert qimen.parse_time("2026-8-1 9:05") == datetime(2026, 8, 1, 9, 5)
    assert qimen.parse_time("2026年8月1日 15：30") == datetime(2026, 8, 1, 15, 30)
    assert qimen.parse_time("2026年8月1日") == datetime(2026, 8, 1, 12, 0)
    assert qimen.parse_time("现在") is None
    assert qimen.parse_time("now") is None
    assert qimen.parse_time("not a time") is None
    assert qimen.parse_time("") is None


def test_qimen_split_time_question():
    assert qimen.split_time_question("出行 2026-08-01 15:30 吉凶") == (
        "2026-08-01 15:30", "出行 吉凶",
    )
    assert qimen.split_time_question("2026年8月1日 15:30 出行") == (
        "2026年8月1日 15:30", "出行",
    )
    assert qimen.split_time_question("明天运势如何") == ("", "明天运势如何")
    assert qimen.split_time_question("现在 出行") == ("", "出行")
    assert qimen.split_time_question("now") == ("", "")


def test_qimen_time_notes():
    text = qimen.build_result("not-a-time", "出行", "测试")
    assert "无法识别" in text
    text2 = qimen.build_result("2026-08-01", "出行", "测试")
    assert "正午" in text2
    text3 = qimen.build_result("", "出行", "测试")
    assert "自动检测当前时刻" in text3
    text4 = qimen.build_result("2026-08-01 15:30", "出行", "测试")
    assert "自动检测" not in text4 and "无法识别" not in text4


def test_qimen_zhongwu_display():
    # 扫描若干时刻：凡值符落中五，简断行必须显示寄坤二
    checked = 0
    for day in range(1, 366):
        d = datetime(2026, 1, 1) + timedelta(days=day - 1)
        pan = qimen.make_pan(d)
        if pan["shi_gan_palace"] == 5:
            checked += 1
            text = qimen.format_pan(pan, "", "")
            assert "中五（寄坤二）" in text
            break
    assert checked >= 1


def test_daily_deterministic():
    d = date(2026, 8, 2)
    t1 = daily.build_result(d, "u1", "小明")
    t2 = daily.build_result(d, "u1", "小明")
    t3 = daily.build_result(d, "u2", "小明")
    assert t1 == t2
    assert t1 != t3
    assert "每日运势" in t1
    assert "塔罗指引" in t1 and "灵签" in t1 and "周易卦象" in t1
    t4 = daily.build_result(date(2026, 8, 3), "u1", "小明")
    assert t4 != t1


def test_render_escaping():
    html = render.build_card_html(
        "标题<题>", "副&题", ["<b>加粗</b> & 符号"], "页脚",
    )
    assert "<b>" not in html
    assert "&lt;b&gt;" in html
    assert "&amp;" in html
    assert "&lt;题&gt;" in html
    html2 = render.build_card_html("t", "s", ['<script>alert("x")</script>'], "f")
    assert "<script>" not in html2
    assert "&lt;script&gt;" in html2
    assert "&quot;x&quot;" in html2
