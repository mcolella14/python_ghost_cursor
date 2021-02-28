import setuptools

setuptools.setup(
    name="pyppeteer_ghost_cursor",
    version="0.1",
    description="Pyppeteer implementation of Xetera/ghost-cursor",
    url="https://github.com/mcolella14/pyppeteer_ghost_cursor",
    author="mcolella14",
    packages=setuptools.find_packages(),
    package_data={"pyppeteer_ghost_cursor": ["js/*.js"]},
    install_requires=["bezier"],
)
