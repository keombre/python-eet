import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="czech-eet",
    version="1.0.1",
    author="Keombre",
    author_email="keombre8@gmail.com",
    description="API for EET",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keombre/python-eet",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "cryptography",
        "lxml"
    ]
)
