import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='python-ballchasing',
    version='0.1',
    author="Rolv-Arild Braaten",
    author_email="rolv_arild@hotmail.com",
    description="Python wrapper for the ballchasing.com API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rolv-Arild/python-ballchasing",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
