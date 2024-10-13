from setuptools import setup, find_packages

setup(
    name="Things",
    version="0.0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic",
    ],
    extras_require={
        "dev": [
            "pytest",
        ],
    },
)