from setuptools import setup, find_packages


test_require = ["logging-formatter", "pytest", "pytest-cov"]

def main():
    """Main method collecting all the parameters to setup."""
    name = "dls-valkyrie-lib"
    version = "3.4.8"
    description = "Python library which implements a simple carrier-independent interface for unidirectional data flow."
    author = "David Erb, KITS - Controls"
    author_email = "KITS@dls.lu.se"
    license = "GPLv3"
    url = "https://gitlab.dls.lu.se/kits-dls/dls-valkyrie-lib-python"
    packages = find_packages(".", exclude=["tests"])
    install_requires = ["pyzmq", "numpy", "setuptools"]

    setup(
        name=name,
        version=version,
        description=description,
        author=author,
        author_email=author_email,
        license=license,
        url=url,
        packages=packages,
        install_requires=install_requires,
        extras_require={"tests": test_require},
    )


if __name__ == "__main__":
    main()
