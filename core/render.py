"""图文卡片渲染（可选功能，渲染失败时主插件会回退到纯文本）。"""
# CSS 长行为有意为之。
from __future__ import annotations

import html as _html


def _esc(value: str) -> str:
    """HTML 转义，防止用户问题文本破坏卡片或注入标记。"""
    return _html.escape(value or "", quote=True)


def build_card_html(
    title: str,
    subtitle: str,
    body_lines: list[str],
    footer: str,
) -> str:
    """把占卜结果渲染成一张暗色神秘风格的卡片 HTML。"""
    body_html = "\n".join(
        f"<div class=\"line {'sep' if not line.strip() else ''}\">{_esc(line)}</div>"
        for line in body_lines
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 640px;
    padding: 36px 40px;
    font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
    color: #e8e3d6;
    background: linear-gradient(160deg, #1a1030 0%, #2b1b4d 45%, #1c1236 100%);
    border-radius: 20px;
  }}
  .card {{
    border: 1px solid rgba(255, 215, 130, 0.35);
    border-radius: 16px;
    padding: 28px 26px;
    background: rgba(20, 12, 40, 0.55);
    box-shadow: 0 0 40px rgba(160, 110, 255, 0.18);
  }}
  .title {{
    font-size: 30px;
    font-weight: 700;
    color: #f3d38a;
    letter-spacing: 2px;
    margin-bottom: 6px;
  }}
  .subtitle {{ font-size: 15px; color: #b9a8dc; margin-bottom: 18px; }}
  .line {{ font-size: 16px; line-height: 1.65; white-space: pre-wrap; word-break: break-all; }}
  .line.sep {{ height: 10px; }}
  .footer {{ margin-top: 18px; font-size: 12px; color: #8f7fb5; border-top: 1px dashed rgba(255,215,130,0.25); padding-top: 12px; }}
</style>
</head>
<body>
<div class="card">
  <div class="title">{_esc(title)}</div>
  <div class="subtitle">{_esc(subtitle)}</div>
  {body_html}
  <div class="footer">{_esc(footer)}</div>
</div>
</body>
</html>"""
