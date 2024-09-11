from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyfilesnap",
    version="0.1.0",
    author="Emile Amajar",
    description="A lightweight Python library for taking and restoring whole-directory snapshots. Supports diff storing and compression.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emilamaj/pyfilesnap",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)