import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read().strip()

setuptools.setup(
    name="securedrop-updater",
    author="SecureDrop Team",
    version=version,
    author_email="securedrop@freedom.press",
    description="SecureDrop Workstation Updater",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="AGPLv3",
    python_requires=">=3.5",
    packages=setuptools.find_packages(exclude=["tests"]),
    url="https://github.com/freedomofpress/securdrop-updater",
    classifiers=[
        "Development Status :: 3 - Beta",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU Affero General Public License v3 (AGPLv3)",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
    ],
)
