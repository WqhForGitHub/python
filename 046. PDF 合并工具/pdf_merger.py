"""
PDF 合并工具
说明：
    - 纯 Python 实现，不使用任何第三方库
    - 因为完整 PDF 标准非常复杂，本 demo 实现了一个简化但
      合法可读的 PDF 子集（PDF 1.4，仅文本页 + Helvetica 字体）
    - 它包括三个核心能力：
        * build_pdf(pages, path)        生成包含若干文本页的 PDF
        * parse_simple_pdf(path)        解析由 build_pdf 生成的 PDF，提取页流
        * merge_pdfs([paths], out_path) 合并多个 PDF
    - 真实场景请使用 PyPDF2 / pypdf / pikepdf 等三方库
"""

import os
import re
import zlib  # 仅占位（本 demo 未启用压缩）


# ====================================================================
# 1) PDF 生成器（从纯文本生成简单 PDF）
# ====================================================================

def _escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list, out_path: str, title: str = "demo"):
    """根据文本页列表生成 PDF
    pages: list[str]  每个字符串是一页的文本（可包含 \n）
    """
    # 预先构造对象内容（不含偏移量）
    # 对象编号约定：
    #   1 -> Catalog
    #   2 -> Pages
    #   3 -> Font (Helvetica)
    #   4..  -> 每页交替: Page / Contents
    objs = {}
    page_obj_ids = []
    next_id = 4
    for text in pages:
        page_id = next_id
        content_id = next_id + 1
        page_obj_ids.append(page_id)
        next_id += 2

        # 构造内容流
        lines = text.split("\n")
        ops = ["BT", "/F1 14 Tf", "1 0 0 1 50 750 Tm", "16 TL"]
        for i, ln in enumerate(lines):
            if i == 0:
                ops.append(f"({_escape_pdf_text(ln)}) Tj")
            else:
                ops.append(f"T*")
                ops.append(f"({_escape_pdf_text(ln)}) Tj")
        ops.append("ET")
        stream = "\n".join(ops) + "\n"
        stream_bytes = stream.encode("latin-1")
        objs[content_id] = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
            + stream_bytes
            + b"\nendstream"
        )
        page_dict = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>"
        )
        objs[page_id] = page_dict.encode("latin-1")

    # Catalog
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    # Pages root
    kids = " ".join(f"{i} 0 R" for i in page_obj_ids)
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_ids)} >>".encode("latin-1")
    # Font
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    # 写文件，记录每个对象的字节偏移
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = {}
    for oid in sorted(objs):
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n".encode("latin-1") + objs[oid] + b"\nendobj\n"

    # xref
    xref_pos = len(out)
    n = max(objs) + 1
    out += f"xref\n0 {n}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for i in range(1, n):
        if i in offsets:
            out += f"{offsets[i]:010d} 00000 n \n".encode("latin-1")
        else:
            out += b"0000000000 00000 f \n"

    # trailer
    out += (
        f"trailer\n<< /Size {n} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode("latin-1")

    with open(out_path, "wb") as f:
        f.write(out)


# ====================================================================
# 2) PDF 解析器（仅识别 build_pdf 生成的简单 PDF）
# ====================================================================

OBJ_RE = re.compile(rb"(\d+)\s+0\s+obj\s*(.*?)\s*endobj", re.DOTALL)


def parse_simple_pdf(path: str) -> dict:
    """解析 PDF，返回 {'objects': {id: bytes}, 'page_ids': [...], 'kids_order': [...]}"""
    with open(path, "rb") as f:
        data = f.read()

    objects = {}
    for m in OBJ_RE.finditer(data):
        oid = int(m.group(1))
        body = m.group(2)
        objects[oid] = body

    # 找到 Pages 对象，提取 Kids
    pages_obj = None
    for oid, body in objects.items():
        if b"/Type /Pages" in body or b"/Type/Pages" in body:
            pages_obj = body
            break
    kids_ids = []
    if pages_obj is not None:
        m = re.search(rb"/Kids\s*\[([^\]]+)\]", pages_obj)
        if m:
            for ref in re.finditer(rb"(\d+)\s+0\s+R", m.group(1)):
                kids_ids.append(int(ref.group(1)))

    return {"objects": objects, "page_ids": kids_ids, "raw": data}


# ====================================================================
# 3) PDF 合并
# ====================================================================

def merge_pdfs(paths: list, out_path: str) -> dict:
    """合并多个简单 PDF 为一个"""
    all_pages = []   # [(page_obj_body, content_obj_body)]

    for p in paths:
        info = parse_simple_pdf(p)
        objs = info["objects"]
        for pid in info["page_ids"]:
            page_body = objs[pid]
            # 提取 Contents 引用
            m = re.search(rb"/Contents\s+(\d+)\s+0\s+R", page_body)
            content_id = int(m.group(1)) if m else None
            if content_id is None or content_id not in objs:
                continue
            all_pages.append((page_body, objs[content_id]))

    # 重新分配对象编号
    new_objects = {}
    new_objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    new_objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    page_ids = []
    next_id = 4
    for page_body, content_body in all_pages:
        new_page_id = next_id
        new_content_id = next_id + 1
        next_id += 2
        page_ids.append(new_page_id)

        # 替换 Contents 引用与 Font 引用为 3 0 R
        new_page_body = re.sub(
            rb"/Contents\s+\d+\s+0\s+R",
            f"/Contents {new_content_id} 0 R".encode("latin-1"),
            page_body,
        )
        new_page_body = re.sub(
            rb"/F1\s+\d+\s+0\s+R", b"/F1 3 0 R", new_page_body
        )
        new_page_body = re.sub(
            rb"/Parent\s+\d+\s+0\s+R", b"/Parent 2 0 R", new_page_body
        )
        new_objects[new_page_id] = new_page_body
        new_objects[new_content_id] = content_body

    kids = " ".join(f"{i} 0 R" for i in page_ids)
    new_objects[2] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
        .encode("latin-1")
    )

    # 写入
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = {}
    for oid in sorted(new_objects):
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n".encode("latin-1") + new_objects[oid] + b"\nendobj\n"

    xref_pos = len(out)
    n = max(new_objects) + 1
    out += f"xref\n0 {n}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for i in range(1, n):
        if i in offsets:
            out += f"{offsets[i]:010d} 00000 n \n".encode("latin-1")
        else:
            out += b"0000000000 00000 f \n"
    out += (
        f"trailer\n<< /Size {n} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode("latin-1")

    with open(out_path, "wb") as f:
        f.write(out)

    return {
        "out": out_path,
        "page_count": len(page_ids),
        "size": len(out),
    }


# ==================== Demo ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  PDF 合并工具 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    a_path = os.path.join(base, "doc_a.pdf")
    b_path = os.path.join(base, "doc_b.pdf")
    c_path = os.path.join(base, "doc_c.pdf")
    out_path = os.path.join(base, "merged.pdf")

    # 1. 生成示例 PDF
    print("\n--- 1. 生成 3 个示例 PDF ---")
    build_pdf(["Document A - Page 1", "Document A - Page 2"], a_path)
    build_pdf(["Document B - Page 1"], b_path)
    build_pdf(["Document C - Page 1", "Document C - Page 2",
               "Document C - Page 3"], c_path)
    for p in (a_path, b_path, c_path):
        info = parse_simple_pdf(p)
        print(f"  {os.path.basename(p):<10} {os.path.getsize(p)} bytes, "
              f"{len(info['page_ids'])} pages")

    # 2. 合并
    print("\n--- 2. 合并 PDF ---")
    res = merge_pdfs([a_path, b_path, c_path], out_path)
    print(f"  输出: {res['out']}")
    print(f"  页数: {res['page_count']}")
    print(f"  大小: {res['size']} bytes")

    # 3. 校验合并结果
    print("\n--- 3. 校验合并后的 PDF ---")
    info = parse_simple_pdf(out_path)
    print(f"  解析到对象数: {len(info['objects'])}")
    print(f"  Pages.Kids 引用: {info['page_ids']}")
    # 浏览器可识别为 6 页
    assert len(info["page_ids"]) == 6, "页数应为 6"
    print("  [OK] 页数校验通过")

    # 4. 简要展示头部
    print("\n--- 4. 输出文件头部预览 ---")
    with open(out_path, "rb") as f:
        head = f.read(160)
    # 用 ascii 只显示可打印部分，避免 Windows GBK 控制台编码问题
    safe = "".join(chr(b) if 32 <= b < 127 or b in (10, 13) else "." for b in head)
    print(safe)

    # 清理
    for p in (a_path, b_path, c_path, out_path):
        if os.path.exists(p):
            os.remove(p)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
