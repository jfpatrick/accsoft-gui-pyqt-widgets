extras = {
    "test": [
        "pytest>=6.2.5,<7a0",
        "pytest-qt>=4.0.2,<5a0",
        "pytest-asyncio>=0.17",
        "mock>=4.0.0;python_version<'3.8'",  # Backport AsyncMock
    ],
    "doc": [
        "Sphinx>=3.2.1,<3.5a0",
    ],
}
