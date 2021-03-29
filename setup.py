import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read().strip()

setuptools.setup(
    name="securedrop-workstation-dom0-config",
    author="SecureDrop Team",
    version=version,
    author_email="securedrop@freedom.press",
    description="SecureDrop Workstation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3+",
    python_requires=">=3.5",
    url="https://github.com/freedomofpress/securdrop-workstation",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: " "GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
)
