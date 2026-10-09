"""纯函数单测 — 不依赖 DB / 网络，直接跑 python -m pytest。"""
from __future__ import annotations

import pytest

from app.utils.files import make_title_from_filename, sanitize_filename
from app.services.reranker_service import LlmReranker, NoReranker


# ==================== sanitize_filename ====================

class TestSanitizeFilename:
    def test_normal(self):
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_basename_strips_path(self):
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("C:\\Users\\x\\file.txt") == "file.txt"

    def test_replaces_illegal_chars(self):
        # basename 先取最后一个路径片段，再替换非法字符
        assert sanitize_filename("a/b:c?d*e") == "b_c_d_e"

    def test_empty_uses_fallback(self):
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"

    def test_no_extension(self):
        assert sanitize_filename("README") == "README"

    def test_path_traversal(self):
        # basename 取最后一段，非法字符替换
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_dots_replaced(self):
        assert sanitize_filename("my..file.txt") == "my_file.txt"


# ==================== make_title_from_filename ====================

class TestMakeTitle:
    def test_strips_extension(self):
        assert make_title_from_filename("hello.pdf") == "hello"

    def test_no_extension(self):
        assert make_title_from_filename("README") == "README"

    def test_empty_fallback(self):
        assert make_title_from_filename("") == "untitled"

    def test_basename_only(self):
        assert make_title_from_filename("/path/to/doc.docx") == "doc"


# ==================== LlmReranker._parse_indices ====================

class TestParseIndices:
    def test_normal(self):
        assert LlmReranker._parse_indices("[0, 2, 5]", 10, 3) == [0, 2, 5]

    def test_duplicates_dedup(self):
        assert LlmReranker._parse_indices("1,1,2", 10, 3) == [1, 2]

    def test_out_of_range_ignored(self):
        assert LlmReranker._parse_indices("99,0,100", 5, 2) == [0]

    def test_top_k_limit(self):
        assert LlmReranker._parse_indices("0,1,2,3,4", 10, 2) == [0, 1]

    def test_empty_text_fallback(self):
        assert LlmReranker._parse_indices("", 5, 3) == [0, 1, 2]

    def test_too_little_fallback(self):
        assert LlmReranker._parse_indices("abc", 5, 3) == [0, 1, 2]


# ==================== NoReranker ====================

@pytest.mark.asyncio
class TestNoReranker:
    async def test_sets_rerank_score_from_distance(self):
        candidates = [
            {"content": "a", "distance": 0.2},
            {"content": "b", "distance": 0.5},
        ]
        result = await NoReranker().rerank("q", candidates, top_k=2)
        scores = [c["rerank_score"] for c in result]
        assert scores == pytest.approx([0.8, 0.5])

    async def test_sorts_by_distance(self):
        candidates = [
            {"content": "far", "distance": 0.9},
            {"content": "near", "distance": 0.1},
        ]
        result = await NoReranker().rerank("q", candidates, top_k=2)
        assert result[0]["content"] == "near"
        assert result[1]["content"] == "far"
