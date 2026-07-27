from setuptools import setup, find_packages

setup(
    name="nuntius",
    version="0.2.1",
    description="Nuntius AI - Um agente de IA completo para Termux",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "httpx>=0.25.0",
        "pyyaml>=6.0",
        "prompt_toolkit>=3.0.0",
    ],
    extras_require={
        "mcp": ["mcp>=1.0.0"],
        "vector": ["chromadb>=0.4.0"],
        "browser": ["playwright>=1.40.0"],
        "telegram": ["python-telegram-bot>=20.0"],
        "discord": ["discord.py>=2.0"],
        "github": ["PyGithub>=1.58"],
        "drive": ["google-api-python-client>=2.0", "google-auth-oauthlib>=1.0"],
        "all": [
            "mcp>=1.0.0",
            "chromadb>=0.4.0",
            "playwright>=1.40.0",
            "python-telegram-bot>=20.0",
            "discord.py>=2.0",
            "PyGithub>=1.58",
            "google-api-python-client>=2.0",
            "google-auth-oauthlib>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nuntius=nuntius.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
)
