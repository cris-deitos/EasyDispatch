from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="easydispatch-collector",
    version="1.0.0",
    description="EasyDispatch DMR Traffic Collector for Raspberry Pi",
    author="EasyDispatch Team",
    author_email="info@easydispatch.local",
    url="https://github.com/cris-deitos/EasyDispatch",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'easydispatch-collector=main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
)
