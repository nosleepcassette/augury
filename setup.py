from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")


setup(
    name="augury",
    version="0.3.0",
    description="Terminal divination suite with tarot, I Ching, a TUI, CLI, and optional Discord formatter.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="cassette, aka maps",
    url="https://github.com/mistermaps/augury",
    project_urls={
        "Homepage": "https://cassette.help",
        "Repository": "https://github.com/mistermaps/augury",
    },
    license="MIT",
    python_requires=">=3.10",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["rich>=13.7"],
    extras_require={"dev": ["pytest>=8.0"]},
    entry_points={
        "console_scripts": [
            "augury=augury.cli:main",
            "augury-discord=augury.discord:main",
            "iching=augury.iching:main",
        ]
    },
    package_data={"augury.systems.iching": ["data/*.js"]},
)
