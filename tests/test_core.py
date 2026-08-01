"""核心逻辑测试：不依赖 AstrBot 运行时。"""
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from cyber_divination.core import lingqian, qimen, tarot, zhouyi


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


def test_lingqian_complete():
    assert len(lingqian.LINGQIAN) == 100
    for _num, (grade, poem, explain) in enumerate(lingqian.LINGQIAN, 1):
        assert grade in ("上上", "上签", "中签", "中平", "下签")
        assert 1 <= poem.count("\n") <= 3
        assert explain


def test_lingqian_draw():
    rng = random.Random(7)
    num, grade, poem, explain = lingqian.draw(rng)
    assert 1 <= num <= 100
    text = lingqian.build_result("考试", "小明")
    assert "签 ·" in text and "签诗" in text and "解曰" in text


def test_tarot_counts():
    assert len(tarot.MAJOR_ARCANA) == 22
    assert sum(len(v) for v in tarot.MINOR_ARCANA.values()) == 56
    assert all(len(v) == 14 for v in tarot.MINOR_ARCANA.values())
    assert len(tarot.ALL_CARDS) == 78


def test_tarot_draw():
    rng = random.Random(1)
    name, rev, meaning = tarot.draw_single(rng)
    assert name and meaning
    spread = tarot.draw_three(rng)
    assert len(spread) == 3
    text = tarot.build_result("three", "感情")
    assert "过去" in text and "未来" in text
    single = tarot.build_result("single")
    assert "单张指引" in single


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
