from setuptools import setup, find_packages

setup(
    name="explainshell-cli",
    version="1.0.0",
    description="A CLI tool that explains shell commands using explainshell.com",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sam",
    author_email="sams@snyk.io",
    url="https://github.com/yourusername/explainshell-cli",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "explainshell-cli = explainshell_cli.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.7',
    include_package_data=True,
)
