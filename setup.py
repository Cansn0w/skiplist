from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = f.read()

with open('LICENSE.txt') as f:
    license = f.read()

setup(
    name='skiplist',
    version='0.1.0',
    author='Chester Liu',
    author_email='chester@cansnow.net',
    description='A skiplist python implementation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Cansn0w/skiplist',
    packages=find_packages(),
    license=license,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
