"""Tests for mineral-pdf-mcp"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers._mock_data import MOCK_PILBARA_RESOURCES


def test_mock_resources_structure():
    """验证 mock 储量数据结构"""
    data = MOCK_PILBARA_RESOURCES
    assert data["project_name"] == "Pilgangoora Lithium-Tantalum Operation"
    assert data["commodity"] == "Lithium (Spodumene)"
    assert data["indicated_tonnage"] > 0
    assert data["indicated_grade"] > 0
    assert data["inferred_tonnage"] > 0
    assert data["inferred_grade"] > 0
    assert data["mock"] is True


def test_mock_resources_json_serializable():
    """验证 mock 储量数据可序列化为 JSON"""
    data = MOCK_PILBARA_RESOURCES
    result = json.dumps(data, ensure_ascii=False)
    parsed = json.loads(result)
    assert parsed["indicated_tonnage"] == 213.0


if __name__ == "__main__":
    test_mock_resources_structure()
    test_mock_resources_json_serializable()
    print("✅ mineral-pdf-mcp tests passed")
