import setuptools

VERSION = "0.0.1"

setuptools.setup(
    name="App",
    version=VERSION,
    author="ZanNen",
    author_email="",
    url="https://github.com/zannen/k8s-apps",
    packages=setuptools.find_packages(),
    package_data={"app": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[],
    setup_requires=["wheel"],
    zip_safe=False,
)
