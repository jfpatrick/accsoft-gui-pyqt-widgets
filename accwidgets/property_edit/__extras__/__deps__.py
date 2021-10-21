extras = {
    "test": [
        "pytest>=4.4.0,<4.5a0",
        "pytest-qt>=3.2.0,<3.3a0",
        "pytest-asyncio",
        "mock>=4.0.0;python_version<'3.8'",  # Backport AsyncMock
    ],
    "doc": [
        "Sphinx>=3.2.1,<3.3a0",
    ],
}
