"""
Markdown 转换器
功能：将 Markdown 文本转换为 HTML，支持标题、段落、列表、代码块、
      表格、链接、图片、粗体、斜体、引用、水平线等
"""

import re
import os


class MarkdownConverter:
    """Markdown 转 HTML 转换器"""

    def __init__(self):
        self.toc = []  # 目录

    def convert(self, markdown: str) -> str:
        """将 Markdown 文本转换为 HTML"""
        self.toc = []

        # 预处理：统一换行符
        markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")

        # 提取代码块（防止内部被转换）
        code_blocks = []
        markdown = self._extract_code_blocks(markdown, code_blocks)

        # 按行处理
        lines = markdown.split("\n")
        html_parts = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 空行
            if not line.strip():
                i += 1
                continue

            # 标题
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = self._inline_convert(heading_match.group(2))
                anchor = self._make_anchor(heading_match.group(2))
                self.toc.append((level, heading_match.group(2), anchor))
                html_parts.append(f'<h{level} id="{anchor}">{text}</h{level}>')
                i += 1
                continue

            # 水平线
            if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line.strip()):
                html_parts.append("<hr>")
                i += 1
                continue

            # 表格
            if (
                "|" in line
                and i + 1 < len(lines)
                and re.match(r"^[\s|:-]+$", lines[i + 1])
            ):
                table_html, i = self._convert_table(lines, i)
                html_parts.append(table_html)
                continue

            # 无序列表
            if re.match(r"^[\s]*[-*+]\s+", line):
                list_html, i = self._convert_unordered_list(lines, i)
                html_parts.append(list_html)
                continue

            # 有序列表
            if re.match(r"^[\s]*\d+\.\s+", line):
                list_html, i = self._convert_ordered_list(lines, i)
                html_parts.append(list_html)
                continue

            # 引用
            if re.match(r"^>\s?", line):
                quote_html, i = self._convert_blockquote(lines, i)
                html_parts.append(quote_html)
                continue

            # 普通段落
            paragraph_lines = []
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(
                    r"^(#{1,6}\s|[-*+]\s|\d+\.\s|>\s?|(-{3,}|\*{3,}|_{3,})\s*$)",
                    lines[i].strip(),
                )
            ):
                paragraph_lines.append(lines[i])
                i += 1
            if paragraph_lines:
                text = self._inline_convert(" ".join(paragraph_lines))
                html_parts.append(f"<p>{text}</p>")

        # 还原代码块
        html = "\n".join(html_parts)
        html = self._restore_code_blocks(html, code_blocks)

        return html

    def convert_file(self, input_path: str, output_path: str = None) -> str:
        """转换 Markdown 文件为 HTML 文件"""
        with open(input_path, "r", encoding="utf-8") as f:
            markdown = f.read()

        html_body = self.convert(markdown)

        # 生成完整 HTML
        html = self._wrap_html(html_body)

        if output_path is None:
            output_path = input_path.rsplit(".", 1)[0] + ".html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"已转换: {input_path} -> {output_path}")
        return output_path

    # ==================== 内部方法 ====================

    def _extract_code_blocks(self, text: str, store: list) -> str:
        """提取代码块，用占位符替换"""
        pattern = r"(```[\s\S]*?```|`[^`]+`)"

        def replacer(match):
            store.append(match.group(0))
            return f"%%CODEBLOCK_{len(store) - 1}%%"

        return re.sub(pattern, replacer, text)

    def _restore_code_blocks(self, html: str, store: list) -> str:
        """还原代码块"""
        for i, block in enumerate(store):
            placeholder = f"%%CODEBLOCK_{i}%%"
            if block.startswith("```"):
                # 多行代码块
                lines = block[3:]  # 去掉开头的 ```
                if lines.endswith("```"):
                    lines = lines[:-3]

                # 提取语言
                first_newline = lines.find("\n")
                if first_newline != -1:
                    lang = lines[:first_newline].strip()
                    code = lines[first_newline + 1 :]
                else:
                    lang = ""
                    code = ""

                code = self._escape_html(code.strip())
                lang_attr = f' class="language-{lang}"' if lang else ""
                code_html = f"<pre><code{lang_attr}>{code}</code></pre>"
                html = html.replace(placeholder, code_html)
            else:
                # 行内代码
                code = self._escape_html(block[1:-1])
                html = html.replace(placeholder, f"<code>{code}</code>")

        return html

    def _inline_convert(self, text: str) -> str:
        """行内元素转换"""
        # 图片（需要在链接之前处理）
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)
        # 链接
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        # 粗斜体
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
        # 粗体
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # 斜体
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # 删除线
        text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
        return text

    def _convert_table(self, lines: list, start: int) -> tuple:
        """转换表格"""
        rows = []
        i = start
        while i < len(lines) and "|" in lines[i]:
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(cells)
            i += 1
            # 第二行是分隔行，跳过
            if len(rows) == 2 and all(
                set(c.strip()) <= {"-", ":", " "} for c in rows[1]
            ):
                align = []
                for c in rows[1]:
                    c = c.strip()
                    if c.startswith(":") and c.endswith(":"):
                        align.append("center")
                    elif c.endswith(":"):
                        align.append("right")
                    else:
                        align.append("left")
                rows.pop(1)  # 移除分隔行
            else:
                align = None

        # 构建 HTML
        if not rows:
            return "", i

        html = "<table>\n"
        # 表头
        html += "  <thead>\n    <tr>\n"
        for cell in rows[0]:
            html += f"      <th>{self._inline_convert(cell)}</th>\n"
        html += "    </tr>\n  </thead>\n"

        # 表体
        if len(rows) > 1:
            html += "  <tbody>\n"
            for row in rows[1:]:
                html += "    <tr>\n"
                for j, cell in enumerate(row):
                    style = (
                        f' style="text-align: {align[j]}"'
                        if align and j < len(align)
                        else ""
                    )
                    html += f"      <td{style}>{self._inline_convert(cell)}</td>\n"
                html += "    </tr>\n"
            html += "  </tbody>\n"

        html += "</table>"
        return html, i

    def _convert_unordered_list(self, lines: list, start: int) -> tuple:
        """转换无序列表"""
        html = "<ul>\n"
        i = start
        while i < len(lines) and re.match(r"^[\s]*[-*+]\s+", lines[i]):
            indent = len(lines[i]) - len(lines[i].lstrip())
            text = re.sub(r"^[\s]*[-*+]\s+", "", lines[i])
            html += f"  <li>{self._inline_convert(text)}</li>\n"
            i += 1
        html += "</ul>"
        return html, i

    def _convert_ordered_list(self, lines: list, start: int) -> tuple:
        """转换有序列表"""
        html = "<ol>\n"
        i = start
        while i < len(lines) and re.match(r"^[\s]*\d+\.\s+", lines[i]):
            text = re.sub(r"^[\s]*\d+\.\s+", "", lines[i])
            html += f"  <li>{self._inline_convert(text)}</li>\n"
            i += 1
        html += "</ol>"
        return html, i

    def _convert_blockquote(self, lines: list, start: int) -> tuple:
        """转换引用块"""
        quote_lines = []
        i = start
        while i < len(lines) and re.match(r"^>\s?", lines[i]):
            quote_lines.append(re.sub(r"^>\s?", "", lines[i]))
            i += 1
        inner = self.convert("\n".join(quote_lines))
        return f"<blockquote>\n{inner}\n</blockquote>", i

    def _make_anchor(self, text: str) -> str:
        """生成锚点"""
        anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.strip().lower())
        return anchor.strip("-")

    def _escape_html(self, text: str) -> str:
        """HTML 转义"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text

    def _wrap_html(self, body: str) -> str:
        """包装为完整 HTML 文档"""
        toc_html = ""
        if self.toc:
            toc_html = "<nav>\n<h2>目录</h2>\n<ul>\n"
            for level, text, anchor in self.toc:
                indent = "  " * (level - 1)
                toc_html += f'{indent}<li><a href="#{anchor}">{text}</a></li>\n'
            toc_html += "</ul>\n</nav>\n"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown 转换结果</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{ margin-top: 1.5em; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
        pre {{ background: #f4f4f4; padding: 16px; border-radius: 6px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        blockquote {{ border-left: 4px solid #ddd; padding-left: 16px; color: #666; margin-left: 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; }}
        th {{ background: #f6f6f6; }}
        img {{ max-width: 100%; }}
        a {{ color: #0366d6; }}
        hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
        nav {{ background: #f8f8f8; padding: 16px; border-radius: 6px; margin-bottom: 2em; }}
    </style>
</head>
<body>
{toc_html}
{body}
</body>
</html>"""


# ==================== 反向转换：HTML → Markdown ====================


class HtmlToMarkdownConverter:
    """HTML 转 Markdown（基础版）"""

    def convert(self, html: str) -> str:
        """将 HTML 转换为 Markdown"""
        # 标题
        for level in range(1, 7):
            html = re.sub(
                rf"<h{level}[^>]*>(.*?)</h{level}>",
                lambda m, l=level: f'{"#" * l} {self._strip_tags(m.group(1))}',
                html,
                flags=re.DOTALL,
            )

        # 粗体
        html = re.sub(r"<strong>(.*?)</strong>", r"**\1**", html, flags=re.DOTALL)
        # 斜体
        html = re.sub(r"<em>(.*?)</em>", r"*\1*", html, flags=re.DOTALL)
        # 删除线
        html = re.sub(r"<del>(.*?)</del>", r"~~\1~~", html, flags=re.DOTALL)
        # 链接
        html = re.sub(
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", html, flags=re.DOTALL
        )
        # 图片
        html = re.sub(
            r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r"![\2](\1)", html
        )
        # 行内代码
        html = re.sub(r"<code>(.*?)</code>", r"`\1`", html, flags=re.DOTALL)
        # 段落
        html = re.sub(r"<p>(.*?)</p>", r"\1\n\n", html, flags=re.DOTALL)
        # 水平线
        html = re.sub(r"<hr\s*/?>", "---", html)
        # 换行
        html = re.sub(r"<br\s*/?>", "\n", html)
        # 列表项
        html = re.sub(r"<li>(.*?)</li>", r"- \1", html, flags=re.DOTALL)

        # 清理多余空白
        html = re.sub(r"\n{3,}", "\n\n", html)
        return html.strip()

    def _strip_tags(self, text: str) -> str:
        """去除 HTML 标签"""
        return re.sub(r"<[^>]+>", "", text)


if __name__ == "__main__":
    # ===== 演示模式 =====
    print("=" * 60)
    print("  Markdown 转换器 Demo")
    print("=" * 60)

    demo_md = """# Markdown 转换器演示

## 基本格式

这是一段普通文本，支持**粗体**、*斜体*、***粗斜体***和~~删除线~~。

## 链接与图片

这是一个[链接示例](https://example.com)，下面是一张图片：

![示例图片](https://example.com/image.png)

## 列表

### 无序列表

- 项目一
- 项目二
- 项目三

### 有序列表

1. 第一步
2. 第二步
3. 第三步

## 代码

行内代码：`print("Hello")`

代码块：

```python
def hello():
    print("Hello, Markdown!")
    return True
```

## 引用

> 这是一段引用文字
> 可以有多行

## 表格

| 姓名 | 年龄 | 城市 |
|:-----|:----:|-----:|
| 张三 | 25 | 北京 |
| 李四 | 30 | 上海 |
| 王五 | 28 | 广州 |

---

## 水平线

以上是一条水平线分隔。
"""

    converter = MarkdownConverter()

    # 转换
    print("\n--- Markdown → HTML 转换 ---\n")
    html = converter.convert(demo_md)
    print(html)

    # 保存为文件
    demo_dir = os.path.dirname(__file__)
    md_path = os.path.join(demo_dir, "demo.md")
    html_path = os.path.join(demo_dir, "demo.html")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(demo_md)

    converter.convert_file(md_path, html_path)

    # HTML → Markdown 反向转换
    print("\n--- HTML → Markdown 反向转换 ---\n")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    reverse_converter = HtmlToMarkdownConverter()
    reversed_md = reverse_converter.convert(html_content)
    print(reversed_md[:500] + "\n...")

    # 清理
    os.remove(md_path)
    os.remove(html_path)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
