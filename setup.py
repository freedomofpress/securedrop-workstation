import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="securedrop-workstation",
    version="0.0.1",
    author="Kushal Das",
    author_email="securedrop@freedom.press",
    description="SecureDrop Workstation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3+",
    python_requires=">=3.5",
    url="https://github.com/freedomofpress/securdrop-workstation",
    data_files = [("share/securedrop-workstation",["config.json.sample"])],
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ),
)
