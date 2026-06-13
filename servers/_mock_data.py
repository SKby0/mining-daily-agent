"""共享 mock 数据 — 所有外部数据源失败时的兜底数据"""

from datetime import datetime, timedelta

TODAY = datetime.now().strftime("%Y-%m-%d")

# ── mining-news-mcp ──────────────────────────────────────────────
MOCK_NEWS: list[dict] = [
    {
        "title": "Pilbara Minerals lifts spodumene output by 4% in FY25",
        "url": "https://www.mining.com/pilbara-minerals-lifts-spodumene-output/",
        "source": "mining.com",
        "date": TODAY,
        "snippet": "Pilbara Minerals reported lithium concentrate production of 820,000–870,000 tonnes for FY2025, exceeding guidance.",
        "mock": True,
    },
    {
        "title": "Lithium spot price continues to pressure hard-rock miners",
        "url": "https://www.miningweekly.com/lithium-spot-price-pressure/",
        "source": "miningweekly.com",
"date": TODAY,
        "snippet": "Lithium carbonate CNY spot fell to ¥170,500/t, squeezing margins for Australian spodumene producers.",
        "mock": True,
    },
    {
        "title": "Pilbara Minerals P2000 expansion pre-feasibility study update",
        "url": "https://www.mining.com/pilbara-p2000-expansion-update/",
        "source": "mining.com",
        "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "snippet": "P2000 expansion to >2 Mtpa spodumene concentrate — pre-feasibility outcomes expected FY27.",
        "mock": True,
    },
    {
        "title": "China NEV sales hit record in May, boosting lithium demand outlook",
        "url": "https://www.mining.com/china-nev-sales-record/",
        "source": "mining.com",
        "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "snippet": "China's new energy vehicle sales reached 1.1 million units in May, up 28% YoY.",
        "mock": True,
    },
    {
        "title": "Albemarle to idle Kemerton lithium hydroxide plant",
        "url": "https://www.miningweekly.com/albemarle-idle-kemerton/",
        "source": "miningweekly.com",
        "date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
        "snippet": "Albemarle announced it will idle its Kemerton WA lithium hydroxide facility amid low prices.",
        "mock": True,
    },
    {
        "title": "Copper prices rally on supply concerns from Panama mine closure",
        "url": "https://www.mining.com/copper-rally-supply-concerns/",
        "source": "mining.com",
        "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "snippet": "COMEX copper futures rose above $4.25/lb as First Quantum's Cobre Panamá remains shuttered.",
        "mock": True,
    },
]

# ── mineral-pdf-mcp ──────────────────────────────────────────────
MOCK_PILBARA_RESOURCES: dict = {
    "project_name": "Pilgangoora Lithium-Tantalum Operation",
    "commodity": "Lithium (Spodumene)",
    "indicated_tonnage": 213.0,
    "indicated_grade": 1.08,
    "inferred_tonnage": 193.0,
    "inferred_grade": 1.04,
    "unit": "Mt @ Li2O%",
    "cutoff_grade": 0.5,
    "source_table_page": "Page 45",
    "report_date": "2023-08-24",
    "mock": True,
}

# ── lme-price-mcp ────────────────────────────────────────────────
MOCK_PRICES: dict[str, dict] = {
    "copper": {"price": 4.25, "unit": "USD/lb", "date": TODAY},
    "nickel": {"price": 16250, "unit": "USD/tonne", "date": TODAY},
    "aluminum": {"price": 2450, "unit": "USD/tonne", "date": TODAY},
    "zinc": {"price": 2780, "unit": "USD/tonne", "date": TODAY},
    "gold": {"price": 2650, "unit": "USD/oz", "date": TODAY},
    "lithium": {"price": 170500, "unit": "CNY/tonne", "date": TODAY},
    "pilbara_stock": {"price": 2.15, "unit": "AUD", "date": TODAY},
}

MOCK_TRENDS: dict[str, dict] = {
    "lithium": {
        "commodity": "lithium",
        "unit": "CNY/tonne",
        "trend_direction": "down",
        "min_price": 150000,
        "max_price": 185000,
        "avg_price": 168000,
        "start_price": 182000,
        "end_price": 170500,
        "change_pct": -6.3,
        "mock": True,
    },
    "pilbara_stock": {
        "commodity": "pilbara_stock",
        "unit": "AUD",
        "trend_direction": "down",
        "min_price": 1.85,
        "max_price": 2.45,
        "avg_price": 2.10,
        "start_price": 2.38,
        "end_price": 2.15,
        "change_pct": -9.7,
        "mock": True,
    },
    "copper": {
        "commodity": "copper",
        "unit": "USD/lb",
        "trend_direction": "up",
        "min_price": 3.95,
        "max_price": 4.35,
        "avg_price": 4.15,
        "start_price": 3.98,
        "end_price": 4.25,
        "change_pct": 6.8,
        "mock": True,
    },
}
