"""
PDF 分割工具
说明：
    - 纯 Python，无第三方依赖
    - 与 46. PDF 合并工具 配套，仅支持本系列简化 PDF (PDF 1.4，文本页)
    - 提供：
        split_pdf(src, out_dir, every=1) -> 按每 N 页一份切割
        extract_pages(src, indices, out) -> 抽取指定页码
        get_page_count(src)
"""

import os
import re


OBJ_RE = re.compile(rb"(\d+)\s+0\s+obj\s*(.*?)\s*endobj", re.DOTALL)


# ====== 复用极简 PDF 生成 / 解析 ======


def _escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list, out_path: str):
    objs = {}
    page_obj_ids = []
    next_id = 4
    for text in pages:
        page_id = next_id
        content_id = next_id + 1
        page_obj_ids.append(page_id)
        next_id += 2

        ops = ["BT", "/F1 14 Tf", "1 0 0 1 50 750 Tm", "16 TL"]
        for i, ln in enumerate(text.split("\n")):
            if i == 0:
                ops.append(f"({_escape_pdf_text(ln)}) Tj")
            else:
                ops.append("T*")
                ops.append(f"({_escape_pdf_text(ln)}) Tj")
        ops.append("ET")
        stream = ("\n".join(ops) + "\n").encode("latin-1")
        objs[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )
        objs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>"
        ).encode("latin-1")

    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{i} 0 R" for i in page_obj_ids)
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_ids)} >>".encode("latin-1")
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for oid in sorted(objs):
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n".encode("latin-1") + objs[oid] + b"\nendobj\n"

    xref_pos = len(out)
    n = max(objs) + 1
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


def parse_simple_pdf(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    objects = {int(m.group(1)): m.group(2)
               for m in OBJ_RE.finditer(data)}
    page_ids = []
    for body in objects.values():
        if b"/Type /Pages" in body or b"/Type/Pages" in body:
            m = re.search(rb"/Kids\s*\[([^\]]+)\]", body)
            if m:
                page_ids = [int(x.group(1))
                            for x in re.finditer(rb"(\d+)\s+0\s+R", m.group(1))]
            break
    return {"objects": objects, "page_ids": page_ids}


def get_page_count(path: str) -> int:
    return len(parse_simple_pdf(path)["page_ids"])


def _write_subset_pdf(src_info: dict, page_indices: list, out_path: str):
    """根据原 PDF 解析结果与页索引列表，写出新 PDF"""
    objs = src_info["objects"]
    src_page_ids = src_info["page_ids"]

    new_objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_ids = []
    next_id = 4
    for idx in page_indices:
        if idx < 0 or idx >= len(src_page_ids):
            continue
        old_pid = src_page_ids[idx]
        page_body = objs[old_pid]
        m = re.search(rb"/Contents\s+(\d+)\s+0\s+R", page_body)
        if not m:
            continue
        old_cid = int(m.group(1))
        if old_cid not in objs:
            continue
        new_pid = next_id
        new_cid = next_id + 1
        next_id += 2
        page_ids.append(new_pid)

        np = re.sub(rb"/Contents\s+\d+\s+0\s+R",
                    f"/Contents {new_cid} 0 R".encode("latin-1"), page_body)
        np = re.sub(rb"/F1\s+\d+\s+0\s+R", b"/F1 3 0 R", np)
        np = re.sub(rb"/Parent\s+\d+\s+0\s+R", b"/Parent 2 0 R", np)
        new_objects[new_pid] = np
        new_objects[new_cid] = objs[old_cid]

    kids = " ".join(f"{i} 0 R" for i in page_ids)
    new_objects[2] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
        .encode("latin-1")
    )

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
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
    return len(page_ids), len(out)


# -------- 公开接口 --------

def extract_pages(src: str, indices: list, out: str) -> dict:
    """抽取页码列表（0-based）到新 PDF"""
    info = parse_simple_pdf(src)
    n, size = _write_subset_pdf(info, indices, out)
    return {"out": out, "pages": n, "size": size}


def split_pdf(src: str, out_dir: str, every: int = 1) -> list:
    """按每 every 页切一份，返回结果列表"""
    info = parse_simple_pdf(src)
    total = len(info["page_ids"])
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    results = []
    chunk_idx = 1
    for start in range(0, total, every):
        idxs = list(range(start, min(start + every, total)))
        out_path = os.path.join(out_dir, f"{base}_part{chunk_idx}.pdf")
        n, size = _write_subset_pdf(info, idxs, out_path)
        results.append({"path": out_path, "pages": n,
                        "indices": idxs, "size": size})
        chunk_idx += 1
    return results


# ==================== Demo ====================

if __name__ == "__main__":
    import shutil

    print("=" * 60)
    print("  PDF 分割工具 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(base, "demo.pdf")
    out_dir = os.path.join(base, "out")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)

    # 1. 生成 7 页 PDF
    print("\n--- 1. 生成测试 PDF ---")
    build_pdf([f"This is page {i+1}" for i in range(7)], src)
    print(f"  生成: {src}, 共 {get_page_count(src)} 页, "
          f"{os.path.getsize(src)} bytes")

    # 2. 每 2 页拆一份
    print("\n--- 2. 每 2 页切一份 ---")
    parts = split_pdf(src, out_dir, every=2)
    for p in parts:
        print(f"  {os.path.basename(p['path'])}  "
              f"pages={p['pages']}  indices={p['indices']}  "
              f"{p['size']} bytes")

    # 3. 抽取指定页（第 1, 3, 5 页 -> 0-based: 0, 2, 4）
    print("\n--- 3. 抽取第 1/3/5 页 ---")
    pick = os.path.join(out_dir, "selected.pdf")
    res = extract_pages(src, [0, 2, 4], pick)
    print(f"  输出: {res['out']}, {res['pages']} 页, {res['size']} bytes")

    # 4. 校验
    print("\n--- 4. 校验 ---")
    for f in os.listdir(out_dir):
        full = os.path.join(out_dir, f)
        n = get_page_count(full)
        print(f"  {f:<24} -> {n} 页")

    # 清理
    if os.path.exists(src):
        os.remove(src)
    shutil.rmtree(out_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
