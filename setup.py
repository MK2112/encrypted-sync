from setuptools import setup, find_packages

setup(
    name="onedrive-pgp",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "python-gnupg>=0.5.0",
        "watchdog>=2.1.9",
        "pyyaml>=6.0",
        "requests>=2.28.1",
        "msal>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "onedrive-pgp=src.main:main",
        ],
    },
    author="MK2112",
    author_email="mk2112@protonmail.com",
    description="A middleman system for PGP encryption of OneDrive files",
    keywords="onedrive, pgp, encryption, security",
    python_requires=">=3.6",
) 