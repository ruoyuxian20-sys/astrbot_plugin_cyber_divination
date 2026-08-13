"""赛博占卜插件：周易六爻 / 观音灵签 / 塔罗牌 / 奇门遁甲 / 每日运势。"""
from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .core import daily, lingqian, qimen, tarot, zhouyi
from .core.render import build_card_html

_GROUP_WORDS = {"divine", "占卜", "zhanbu"}
_SUB_WORDS = {
    "zhouyi", "六爻", "周易", "摇卦",
    "lingqian", "灵签", "观音灵签", "签",
    "tarot", "塔罗", "塔罗牌", "牌",
    "qimen", "奇门", "奇门遁甲", "遁甲",
    "daily", "每日", "运势",
    "history", "历史", "记录",
    "help", "帮助", "菜单", "usage",
}

_MAX_QUESTION = 120
_LLM_FAIL_COOLDOWN = 60

_HELP_TEXT = """🔮 赛博占卜使用说明

/占卜 六爻 [所问之事]
    三枚铜钱起卦，含六神、本卦与变卦
/占卜 灵签 [所问之事]
    观音灵签一百签
/占卜 塔罗 [单张|三张] [所问之事]
    单张指引或过去/现在/未来牌阵（不重复抽牌）
/占卜 塔罗 查 [关键词]
    查询塔罗牌牌意，如：/占卜 塔罗 查 星星
/占卜 奇门 [所问之事]
    简式时家奇门排盘；不填时间自动用当前时刻，
    也可指定：/占卜 奇门 YYYY-MM-DD HH:MM [所问之事]
/占卜 每日
    每日运势（塔罗+灵签+周易），当天固定、明日刷新
/占卜 历史 [清除]
    查看或清除本会话占卜记录
/占卜 帮助
    查看本说明

示例：
/占卜 六爻 明天适合出门吗
/占卜 塔罗 三张 感情运
/占卜 奇门 出行吉凶
/占卜 塔罗 查 星星"""


class CyberDivination(Star):
    """赛博占卜：传统占卜体系的娱乐实现。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    # ---------- 工具 ----------

    def _cfg(self, key: str, default):
        try:
            return self.config.get(key, default)
        except Exception:
            return default

    def _sender(self, event: AstrMessageEvent) -> str:
        try:
            return event.get_sender_name() or ""
        except Exception:
            return ""

    def _sender_id(self, event: AstrMessageEvent) -> str:
        try:
            return str(event.get_sender_id() or "")
        except Exception:
            return ""

    def _remainder(self, event: AstrMessageEvent) -> str:
        """去掉唤醒前缀、命令组和子命令，返回剩余内容（所问之事等）。"""
        try:
            text = event.get_message_str().strip()
        except Exception:
            text = ""
        text = re.sub(r"\[CQ:[^\]]*\]", "", text).strip()
        tokens = text.split()
        if tokens and (tokens[0].startswith(("/", "／", "@"))):
            tokens = tokens[1:]
        dropped = 0
        all_words = _GROUP_WORDS | _SUB_WORDS
        while tokens and dropped < 2:
            token = tokens[0].strip("，,。.！!？?")
            if token.lower() not in all_words:
                break
            tokens = tokens[1:]
            dropped += 1
        return " ".join(tokens).strip()[:_MAX_QUESTION]

    async def _record_history(self, event: AstrMessageEvent, kind: str, summary: str):
        """记录一条占卜历史（kv 列表，超出上限截断；失败静默不影响主流程）。"""
        try:
            key = f"history_{event.unified_msg_origin}"
            items = await self.get_kv_data(key, []) or []
            if not isinstance(items, list):
                items = []
            try:
                limit = max(1, int(self._cfg("history_max", 10)))
            except Exception:
                limit = 10
            items.append({
                "t": time.strftime("%m-%d %H:%M"),
                "kind": kind,
                "summary": summary,
            })
            await self.put_kv_data(key, items[-limit:])
        except Exception:
            pass

    async def _maybe_llm(self, event: AstrMessageEvent, title: str, body: str) -> str:
        """可选 LLM 润色：开启 + 冷却通过时调用模型，任何失败都回退原文。"""
        if not self._cfg("llm_enabled", False):
            return body
        try:
            cooldown = max(0, int(self._cfg("llm_cooldown_seconds", 300)))
        except Exception:
            cooldown = 300
        umo = event.unified_msg_origin
        now = time.time()
        try:
            last = float(await self.get_kv_data(f"llm_cd_{umo}", 0) or 0)
            fail = float(await self.get_kv_data(f"llm_fail_cd_{umo}", 0) or 0)
            if now - last < cooldown or now - fail < _LLM_FAIL_COOLDOWN:
                return body
        except Exception:
            pass
        try:
            try:
                timeout = max(5, int(self._cfg("llm_timeout_seconds", 30)))
            except Exception:
                timeout = 30
            provider_id = await self.context.get_current_chat_provider_id(umo)
            resp = await asyncio.wait_for(
                self.context.llm_generate(
                    chat_provider_id=provider_id,
                    system_prompt=(
                        "你是一位精通传统术数的占卜师，风格温和幽默、点到为止。"
                        "请根据基础占卜结果，用 80-150 字给出个性化解读与建议，"
                        "并提醒仅供参考娱乐，不要给出绝对化结论。"
                    ),
                    prompt=f"以下是【{title}】的占卜结果：\n\n{body}\n\n请给出个性化解读。",
                    temperature=0.85,
                ),
                timeout=timeout,
            )
            text = (resp.completion_text or "").strip()
            text = re.sub(r"\[CQ:[^\]]*\]", "", text)
            text = re.sub(r'^["「『“]|["」』”]$', "", text).strip()
            if text:
                try:
                    await self.put_kv_data(f"llm_cd_{umo}", int(now))
                except Exception:
                    pass
                return body + "\n\n🔮 AI 解读：" + text
        except Exception as e:
            logger.warning(f"cyber_divination LLM 润色失败，回退内置解读: {e}")
            try:
                await self.put_kv_data(f"llm_fail_cd_{umo}", int(now))
            except Exception:
                pass
        return body

    async def _finish(
        self,
        event: AstrMessageEvent,
        title: str,
        body: str,
        subtitle: str = "",
    ):
        """统一输出：先尝试 LLM 润色，再按配置输出图片或文本。"""
        body = await self._maybe_llm(event, title, body)
        if self._cfg("use_image", False):
            try:
                url = await self.html_render(
                    build_card_html(
                        title,
                        subtitle,
                        body.splitlines(),
                        "赛博占卜 · 仅供娱乐",
                    ),
                    {},
                )
                yield event.image_result(url)
                return
            except Exception as e:
                logger.warning(f"cyber_divination 图片渲染失败，回退纯文本: {e}")
        yield event.plain_result(body)

    async def _run(self, event: AstrMessageEvent, title: str, subtitle: str, body: str):
        try:
            async for result in self._finish(event, title, body, subtitle):
                yield result
        except Exception as e:
            logger.error(f"cyber_divination {title} 处理异常: {e}")
            yield event.plain_result("占卜出了点小问题，请稍后再试～")

    # ---------- 命令组 ----------

    @filter.command_group("divine", alias={"占卜", "zhanbu"})
    def divine():
        """赛博占卜：/占卜 六爻|灵签|塔罗|奇门|每日|历史|帮助"""

    @divine.command("help", alias={"帮助", "菜单"})
    async def help_cmd(self, event: AstrMessageEvent):
        """查看赛博占卜使用说明"""
        yield event.plain_result(_HELP_TEXT)

    @divine.command("zhouyi", alias={"六爻", "周易", "摇卦"})
    async def zhouyi_cmd(self, event: AstrMessageEvent):
        """周易六爻：铜钱起卦（含六神）。用法：/占卜 六爻 [所问之事]"""
        cast = zhouyi.cast()
        body = zhouyi.format_cast(
            cast,
            question=self._remainder(event),
            sender=self._sender(event),
        )
        await self._record_history(event, "六爻", zhouyi.summarize(cast))
        async for result in self._run(event, "周易六爻", "三枚铜钱 · 六爻成卦", body):
            yield result

    @divine.command("lingqian", alias={"灵签", "观音灵签", "签"})
    async def lingqian_cmd(self, event: AstrMessageEvent):
        """观音灵签。用法：/占卜 灵签 [所问之事]"""
        number, grade, poem, explain = lingqian.draw()
        body = lingqian.format_draw(
            number, grade, poem, explain,
            question=self._remainder(event),
            sender=self._sender(event),
        )
        await self._record_history(event, "灵签", f"第{number}签 · {grade}")
        # 今日求签次数（按天重置，纯趣味，失败不影响）
        try:
            key = f"daily_lingqian_{event.unified_msg_origin}_{time.strftime('%Y%m%d')}"
            count = await self.get_kv_data(key, 0) or 0
            count += 1
            await self.put_kv_data(key, count)
            body += f"\n（今日第 {count} 次求签）"
        except Exception:
            pass
        async for result in self._run(event, "观音灵签", "灵签一签 · 心诚则灵", body):
            yield result

    @divine.command("tarot", alias={"塔罗", "塔罗牌", "牌"})
    async def tarot_cmd(self, event: AstrMessageEvent):
        """塔罗牌。用法：/占卜 塔罗 [单张|三张] [所问之事] ｜ /占卜 塔罗 查 [关键词]"""
        remainder = self._remainder(event)
        search = re.match(r"^(查询|牌意|查)\b", remainder)
        if search:
            keyword = remainder[search.end():].strip()
            if not keyword:
                yield event.plain_result(
                    "用法：/占卜 塔罗 查 [关键词]，例如 /占卜 塔罗 查 星星"
                )
                return
            hits = tarot.search_cards(keyword)
            if not hits:
                yield event.plain_result(
                    "没有找到相关牌，试试中文牌名或英文关键词，例如「星星」或「star」。"
                )
                return
            lines = ["🔮 塔罗牌查牌结果："]
            shown = hits[:10]
            for name, upright, reversed_ in shown:
                lines.append(f"【{name}】")
                lines.append(f"  正位：{upright}")
                lines.append(f"  逆位：{reversed_}")
                lines.append("")
            if len(hits) > len(shown):
                lines.append(f"……共 {len(hits)} 张匹配，请缩小关键词范围。")
            yield event.plain_result("\n".join(lines))
            return

        spread, question = tarot.parse_spread(remainder)
        if spread == "three":
            cards = tarot.draw_three()
            body = tarot.format_three(cards, question, self._sender(event))
            summary = " · ".join(
                tarot.card_summary(name, is_reversed)
                for _pos, name, is_reversed, _meaning in cards
            )
        else:
            name, is_reversed, meaning = tarot.draw_single()
            body = tarot.format_single(name, is_reversed, meaning, question, self._sender(event))
            summary = tarot.card_summary(name, is_reversed)
        await self._record_history(event, "塔罗", summary)
        subtitle = "过去 · 现在 · 未来" if spread == "three" else "单张指引"
        async for result in self._run(event, "塔罗牌占卜", subtitle, body):
            yield result

    @divine.command("qimen", alias={"奇门", "奇门遁甲", "遁甲"})
    async def qimen_cmd(self, event: AstrMessageEvent):
        """奇门遁甲（简式时家）。用法：/占卜 奇门 [所问之事]，不填时间自动用当前时刻"""
        remainder = self._remainder(event)
        time_str, question = qimen.split_time_question(remainder)
        provided = bool(time_str.strip())
        parsed = qimen.parse_time(time_str)
        invalid = provided and parsed is None
        dt = parsed or datetime.now()
        pan = qimen.make_pan(dt)
        if invalid:
            note = "⚠ 时间格式无法识别，已按当前时刻起局。"
        elif not provided:
            note = "（自动检测当前时刻起局）"
        elif qimen.is_date_only(time_str):
            note = "（仅提供日期，按当日正午起局）"
        else:
            note = ""
        body = qimen.format_pan(pan, question, self._sender(event), note=note)
        await self._record_history(event, "奇门", qimen.summarize(pan))
        subtitle = f"自动起局 · {dt:%m-%d %H:%M}" if not provided else f"{dt:%m-%d %H:%M}"
        async for result in self._run(event, "奇门遁甲", subtitle, body):
            yield result

    @divine.command("daily", alias={"每日", "运势"})
    async def daily_cmd(self, event: AstrMessageEvent):
        """每日运势：/占卜 每日。当天结果固定，明日刷新"""
        uid = self._sender_id(event) or event.unified_msg_origin
        body = daily.build_result(uid=uid, uid_name=self._sender(event))
        await self._record_history(event, "每日", "每日运势")
        async for result in self._run(event, "每日运势", "塔罗 · 灵签 · 周易", body):
            yield result

    @divine.command("history", alias={"历史", "记录"})
    async def history_cmd(self, event: AstrMessageEvent):
        """占卜历史：/占卜 历史 [清除]"""
        remainder = self._remainder(event)
        key = f"history_{event.unified_msg_origin}"
        if remainder.strip() in {"清除", "clear"}:
            try:
                await self.put_kv_data(key, [])
                yield event.plain_result("占卜历史已清除。")
            except Exception:
                yield event.plain_result("历史清除失败，请稍后再试～")
            return
        try:
            items = await self.get_kv_data(key, []) or []
        except Exception:
            items = []
        if not isinstance(items, list) or not items:
            yield event.plain_result("还没有占卜记录，先来一卦吧～")
            return
        lines = ["🔮 占卜历史（最近优先）："]
        for i, item in enumerate(items, 1):
            try:
                lines.append(
                    f"{i}. [{item['t']}] {item['kind']} · {item['summary']}"
                )
            except Exception:
                continue
        lines.append("")
        lines.append("清除记录：/占卜 历史 清除")
        yield event.plain_result("\n".join(lines))

    async def terminate(self):
        logger.info("cyber_divination 插件已停止")
