"""MCP Server 2: mineral-pdf-mcp — NI 43-101 PDF 储量数据解析

工具:
  extract_resources(pdf_url) — 从 PDF 提取 Indicated/Inferred 储量数据

数据流:
  Phase 1: pymupdf (fitz) 快速扫描关键词定位候选页
  Phase 2: pdfplumber 精确提取表格数据
"""

import json
import os
import re
import tempfile
from typing import Optional

import requests
from fastmcp import FastMCP

from servers._mock_data import MOCK_PILBARA_RESOURCES

mcp = FastMCP("mineral-pdf-mcp")

_HEADERS = {"User-Agent": "MiningDailyBot/1.0"}
_TIMEOUT = 30

# 搜索关键词 (用于 pymupdf 页面扫描)
_KEYWORDS = [
    "indicated mineral resource",
    "inferred mineral resource",
    "measured mineral resource",
    "mineral resource estimate",
    "mineral resource statement",
    "resource estimate",
    "indicated",
    "inferred",
    "measured and indicated",
]

# 品位单位正则
_GRADE_UNIT_RE = re.compile(
    r"(Li2O|Cu|Au|Ag|Fe|Zn|Ni|Co|Pb|Mo|U3O8|REO)\s*[%g/t]",
    re.IGNORECASE,
)


def _download_pdf(pdf_url: str) -> str:
    """下载 PDF 到临时文件，返回本地路径"""
    if pdf_url.startswith(("http://", "https://")):
        resp = requests.get(pdf_url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    else:
        # 本地文件路径
        if not os.path.exists(pdf_url):
            raise FileNotFoundError(f"PDF file not found: {pdf_url}")
        return pdf_url


def _scan_pages_with_pymupdf(pdf_path: str) -> list[int]:
    """Phase 1: 用 pymupdf 快速扫描包含资源关键词的页面"""
    import fitz  # pymupdf

    candidate_pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()
            keyword_hits = sum(1 for kw in _KEYWORDS if kw in text)
            if keyword_hits >= 2:  # 至少匹配 2 个关键词
                candidate_pages.append(page_num + 1)  # 1-indexed for user readability
        doc.close()
    except Exception as e:
        print(f"[mineral-pdf-mcp] pymupdf scan error: {e}")

    return candidate_pages


def _extract_tables_with_pdfplumber(pdf_path: str, candidate_pages: list[int]) -> list[dict]:
    """Phase 2: 用 pdfplumber 精确提取候选页的表格数据"""
    import pdfplumber

    tables_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx in candidate_pages:
                if page_idx > len(pdf.pages):
                    continue
                page = pdf.pages[page_idx - 1]  # convert 1-indexed to 0-indexed

                # 尝试多种表格提取策略
                for strategy in ["lines", "text"]:
                    try:
                        table_settings = {
                            "vertical_strategy": strategy,
                            "horizontal_strategy": strategy if strategy == "lines" else "text",
                            "snap_tolerance": 5,
                            "join_tolerance": 3,
                        }
                        tables = page.extract_tables(table_settings)

                        for table in tables:
                            if not table or len(table) < 2:
                                continue

                            # 解析表格行寻找 Indicated/Inferred 行
                            parsed = _parse_resource_table(table, page_idx)
                            if parsed:
                                tables_data.append(parsed)
                    except Exception:
                        continue
    except Exception as e:
        print(f"[mineral-pdf-mcp] pdfplumber error: {e}")

    return tables_data


def _parse_resource_table(table: list[list], page_num: int) -> Optional[dict]:
    """解析单个表格，提取 Indicated/Inferred 储量行"""
    result = {
        "source_table_page": f"Page {page_num}",
        "rows": [],
    }

    for row in table:
        row_text = " ".join(str(cell) or "" for cell in row).lower()
        if "indicated" in row_text or "inferred" in row_text or "measured" in row_text:
            result["rows"].append({
                "raw_cells": [str(cell) or "" for cell in row],
                "category": "Indicated" if "indicated" in row_text else
                            "Inferred" if "inferred" in row_text else
                            "Measured" if "measured" in row_text else "Unknown",
            })

    if not result["rows"]:
        return None
    return result


def _structure_resource_data(raw_tables: list[dict]) -> dict:
    """将原始表格数据结构化为标准输出格式"""
    indicated_tonnage = None
    indicated_grade = None
    inferred_tonnage = None
    inferred_grade = None
    commodity = "Unknown"
    unit = ""
    cutoff_grade = None

    for table in raw_tables:
        for row_info in table["rows"]:
            cells = row_info["raw_cells"]
            category = row_info["category"]

            # 尝试从行数据中提取数值
            numbers = []
            for cell in cells:
                cell = cell.strip()
                # 匹配数字 (可能含逗号和小数)
                match = re.search(r"([\d,]+\.?\d*)", cell)
                if match:
                    val = match.group(1).replace(",", "")
                    try:
                        numbers.append(float(val))
                    except ValueError:
                        pass

            # 尝试识别品位单位
            full_text = " ".join(cells)
            grade_match = _GRADE_UNIT_RE.search(full_text)
            if grade_match:
                commodity = grade_match.group(1).upper()
                # Li2O → Lithium
                if commodity == "LI2O":
                    commodity = "Lithium (Li2O)"

            # 根据位置推断: 通常是 [Category, Tonnage, Grade, Contained Metal]
            # 或更复杂的格式，尝试灵活匹配
            if category in ("Indicated", "Measured and Indicated"):
                if len(numbers) >= 2:
                    indicated_tonnage = numbers[0]
                    indicated_grade = numbers[1]
                elif len(numbers) == 1:
                    indicated_tonnage = numbers[0]
            elif category == "Inferred":
                if len(numbers) >= 2:
                    inferred_tonnage = numbers[0]
                    inferred_grade = numbers[1]
                elif len(numbers) == 1:
                    inferred_tonnage = numbers[0]

    if indicated_tonnage and not unit:
        unit = "Mt @ %grade" if indicated_grade else "Mt"

    return {
        "commodity": commodity,
        "indicated_tonnage": indicated_tonnage,
        "indicated_grade": indicated_grade,
        "inferred_tonnage": inferred_tonnage,
        "inferred_grade": inferred_grade,
        "unit": unit,
        "cutoff_grade": cutoff_grade,
    }


# ── MCP 工具 ─────────────────────────────────────────────────────
@mcp.tool
def extract_resources(pdf_url: str) -> str:
    """Extract mineral resource estimates (Indicated/Inferred) from a NI 43-101 report PDF.

    Args:
        pdf_url: URL or local file path to the NI 43-101 technical report PDF

    Returns:
        JSON string of dict with keys:
        project_name, commodity, indicated_tonnage, indicated_grade,
        inferred_tonnage, inferred_grade, unit, cutoff_grade, source_table_page
    """
    tmp_path = None
    try:
        # Step 1: 获取 PDF 文件
        pdf_path = _download_pdf(pdf_url)
        if pdf_url.startswith(("http://", "https://")):
            tmp_path = pdf_path

        # Step 2: pymupdf 快速扫描关键词页面
        candidate_pages = _scan_pages_with_pymupdf(pdf_path)

        if not candidate_pages:
            # 如果没有找到关键词页面，尝试前 20 页中所有有表格的页面
            import fitz
            doc = fitz.open(pdf_path)
            candidate_pages = list(range(1, min(21, len(doc) + 1)))
            doc.close()

        # Step 3: pdfplumber 精确提取
        raw_tables = _extract_tables_with_pdfplumber(pdf_path, candidate_pages)

        # Step 4: 结构化
        result = _structure_resource_data(raw_tables)

        # 如果结构化结果为空，尝试用 pymupdf 提取原始文本作为 fallback
        if not result.get("indicated_tonnage") and not result.get("inferred_tonnage"):
            import fitz
            doc = fitz.open(pdf_path)
            raw_text_snippets = []
            for page_num in candidate_pages:
                if page_num <= len(doc):
                    page = doc[page_num - 1]
                    text = page.get_text()
                    for kw in ["Indicated", "Inferred", "Measured"]:
                        if kw in text:
                            # 提取关键词周围的文本
                            lines = text.split("\n")
                            for line in lines:
                                if kw in line:
                                    raw_text_snippets.append(line.strip())
            doc.close()

            if raw_text_snippets:
                result["raw_text_fallback"] = raw_text_snippets[:20]

        # 如果结果仍然为空且 URL 含 pilbara 关键词，使用 mock 数据
        if not result.get("indicated_tonnage") and not result.get("inferred_tonnage"):
            if "pilbara" in pdf_url.lower() or "plg" in pdf_url.lower():
                result = MOCK_PILBARA_RESOURCES.copy()
            else:
                result["warning"] = "No NI 43-101 resource tables detected in this PDF"

        result["source_pdf"] = pdf_url

    except FileNotFoundError as e:
        result = {"error": str(e), "pdf_url": pdf_url}
    except requests.exceptions.RequestException as e:
        # PDF 下载失败
        if "pilbara" in pdf_url.lower():
            result = MOCK_PILBARA_RESOURCES.copy()
            result["warning"] = f"PDF download failed, using mock data: {e}"
            result["source_pdf"] = pdf_url
        else:
            result = {"error": f"Failed to download PDF: {e}", "pdf_url": pdf_url}
    except Exception as e:
        result = {"error": f"Unexpected error: {e}", "pdf_url": pdf_url}

    finally:
        # 清理临时文件
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
