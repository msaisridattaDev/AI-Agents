from setuptools import setup, find_packages

setup(
    name="ai-coding-assistant",
    version="0.1.0",
    description="A production-grade AI coding assistant",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.8.0",
        "openai>=1.0.0",
        "langchain>=0.1.0",
        "pydantic>=2.0.0",
        "flask>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-coding-assistant=src.main:main",
        ],
    },
    python_requires=">=3.10",
)
