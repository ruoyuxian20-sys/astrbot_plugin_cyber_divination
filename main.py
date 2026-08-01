"""赛博占卜插件：周易六爻 / 观音灵签 / 塔罗牌 / 奇门遁甲。"""
from __future__ import annotations

import asyncio
import re
import time

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .core import lingqian, qimen, tarot, zhouyi
from .core.render import build_card_html

_GROUP_WORDS = {"divine", "占卜", "zhanbu"}
_SUB_WORDS = {
    "zhouyi", "六爻", "周易", "摇卦",
    "lingqian", "灵签", "观音灵签", "签",
    "tarot", "塔罗", "塔罗牌", "牌",
    "qimen", "奇门", "奇门遁甲", "遁甲",
    "help", "帮助", "菜单", "usage",
}

_HELP_TEXT = """🔮 赛博占卜使用说明

/占卜 六爻 [所问之事]
    三枚铜钱起卦，断本卦变卦
/占卜 灵签 [所问之事]
    观音灵签一百签
/占卜 塔罗 [单张|三张] [所问之事]
    单张指引或过去/现在/未来牌阵
/占卜 奇门 [YYYY-MM-DD HH:MM] [所问之事]
    简式时家奇门排盘，不填时间用当前时间
/占卜 帮助
    查看本说明

示例：
/占卜 六爻 明天适合出门吗
/占卜 塔罗 三张 感情运
/占卜 奇门 2026-08-01 15:30 出行吉凶"""


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

    def _remainder(self, event: AstrMessageEvent) -> str:
        """去掉唤醒前缀、命令组和子命令，返回剩余内容（所问之事等）。"""
        try:
            text = event.get_message_str().strip()
        except Exception:
            text = ""
        tokens = text.split()
        if tokens and (tokens[0].startswith("/") or tokens[0].startswith("@")):
            tokens = tokens[1:]
        dropped = 0
        all_words = _GROUP_WORDS | _SUB_WORDS
        while tokens and dropped < 2:
            token = tokens[0].strip("，,。.！!？?")
            if token.lower() not in all_words:
                break
            tokens = tokens[1:]
            dropped += 1
        return " ".join(tokens).strip()

    async def _maybe_llm(self, event: AstrMessageEvent, title: str, body: str) -> str:
        """可选 LLM 润色：开启 + 冷却通过时调用模型，任何失败都回退原文。"""
        if not self._cfg("llm_enabled", False):
            return body
        cooldown = max(0, int(self._cfg("llm_cooldown_seconds", 300)))
        umo = event.unified_msg_origin
        now = time.time()
        try:
            last = await self.get_kv_data(f"llm_cd_{umo}", 0) or 0
            if now - last < cooldown:
                return body
        except Exception:
            pass
        try:
            provider_id = await self.context.get_current_chat_provider_id(umo)
            timeout = max(5, int(self._cfg("llm_timeout_seconds", 30)))
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
            if text:
                try:
                    await self.put_kv_data(f"llm_cd_{umo}", int(now))
                except Exception:
                    pass
                return body + "\n\n🔮 AI 解读：" + text
        except Exception as e:
            logger.warning(f"cyber_divination LLM 润色失败，回退内置解读: {e}")
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
        """赛博占卜：/占卜 六爻|灵签|塔罗|奇门|帮助"""
        pass

    @divine.command("help", alias={"帮助", "菜单"})
    async def help_cmd(self, event: AstrMessageEvent):
        """查看赛博占卜使用说明"""
        yield event.plain_result(_HELP_TEXT)

    @divine.command("zhouyi", alias={"六爻", "周易", "摇卦"})
    async def zhouyi_cmd(self, event: AstrMessageEvent):
        """周易六爻：铜钱起卦。用法：/占卜 六爻 [所问之事]"""
        body = zhouyi.build_result(
            question=self._remainder(event),
            sender=self._sender(event),
        )
        async for result in self._run(event, "周易六爻", "三枚铜钱 · 六爻成卦", body):
            yield result

    @divine.command("lingqian", alias={"灵签", "观音灵签", "签"})
    async def lingqian_cmd(self, event: AstrMessageEvent):
        """观音灵签。用法：/占卜 灵签 [所问之事]"""
        body = lingqian.build_result(
            question=self._remainder(event),
            sender=self._sender(event),
        )
        # 今日求签次数（纯趣味，失败不影响）
        try:
            key = f"daily_lingqian_{event.unified_msg_origin}"
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
        """塔罗牌。用法：/占卜 塔罗 [单张|三张] [所问之事]"""
        remainder = self._remainder(event)
        spread = "three" if re.match(r"^(三张|3|three)\b", remainder) else "single"
        if spread == "three":
            remainder = re.sub(r"^(三张|3|three)\b", "", remainder).strip()
        body = tarot.build_result(
            spread=spread,
            question=remainder,
            sender=self._sender(event),
        )
        subtitle = "过去 · 现在 · 未来" if spread == "three" else "单张指引"
        async for result in self._run(event, "塔罗牌占卜", subtitle, body):
            yield result

    @divine.command("qimen", alias={"奇门", "奇门遁甲", "遁甲"})
    async def qimen_cmd(self, event: AstrMessageEvent):
        """奇门遁甲（简式时家）。用法：/占卜 奇门 [YYYY-MM-DD HH:MM] [所问之事]"""
        remainder = self._remainder(event)
        time_str, question = self._split_qimen(remainder)
        body = qimen.build_result(
            time_str=time_str,
            question=question,
            sender=self._sender(event),
        )
        subtitle = time_str or "当前时刻"
        async for result in self._run(event, "奇门遁甲", subtitle, body):
            yield result

    # ---------- 私有 ----------

    @staticmethod
    def _split_qimen(remainder: str) -> tuple[str, str]:
        """从剩余文本中提取时间与所问之事。"""
        match = re.search(
            r"\d{4}[-/]\d{1,2}[-/]\d{1,2}" r"(?:\s+\d{1,2}:\d{2})?",
            remainder,
        )
        if not match:
            return "", remainder
        time_str = match.group(0)
        question = (remainder[: match.start()] + " " + remainder[match.end():]).strip()
        return time_str, question

    async def terminate(self):
        logger.info("cyber_divination 插件已停止")
