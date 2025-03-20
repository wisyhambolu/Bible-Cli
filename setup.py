from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bible-cli",
    version="1.0.2",
    author="Wisdom Hambolu",
    author_email="wisyhambolu@gmail.com",
    description="A command-line interface for reading and searching the Bible",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wisyhambolu/Bible-Cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Religion",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich==13.7.0",
        "rapidfuzz==3.6.1",
    ],
    entry_points={
        "console_scripts": [
            "bible=bible_cli.bible_cli:main",
        ],
    },
    package_data={
        "bible_cli": ["dataset.json"],
    },
) 
