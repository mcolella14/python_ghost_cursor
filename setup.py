import pathlib
import setuptools

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()
setuptools.setup(
    name="pyppeteer_ghost_cursor",
    version="0.2.2",
    description="Pyppeteer implementation of Xetera/ghost-cursor",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/mcolella14/pyppeteer_ghost_cursor",
    author="mcolella14",
    author_email="mcolella14@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={"pyppeteer_ghost_cursor": ["js/*.js"]},
    install_requires=["bezier"],
    classifiers=[
        "Development Status :: 7 - Inactive",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
