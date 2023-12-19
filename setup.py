import setuptools

from ballchasing import __version__, __author__, __email__, __description__, __url__, __download_url__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='python-ballchasing',
    version=__version__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=__url__,
    download_url=__download_url__,
    install_requires=["requests"],
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    package_data={'ballchasing': ['*.tsv']},
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
