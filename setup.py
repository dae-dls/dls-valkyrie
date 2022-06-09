from setuptools import setup, find_packages


def main():
    name = "dls-valkyrie"
    version = "4.1.1"
    description = "Valkyrie library."
    author = "David Erb"
    author_email = "david.erb@diamond.ac.uk"
    license = "GPLv3"
    url = "https://github.com"
    packages = find_packages(exclude=["tests", "*.tests.*", "tests.*", "tests"])
    install_requires = ["pyzmq", "numpy", "setuptools"]
    include_package_data = True

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
        include_package_data=include_package_data,
    )


if __name__ == "__main__":
    main()
