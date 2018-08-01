import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="artmr",
    version="1.0-beta2",
    author="mronkain",
    author_email="mrnk@iki.fi",
    description="Offline race timing console application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mronkain/artmr",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2.7",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',        
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities"
    ),
    install_requires=[
        'asciimatics>=1.9',
        'sqlobject',
        'pandas'
    ],
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, <4',
    entry_points = {
        'console_scripts': ['artmr=artmr.artmr:main'],
    }


)
