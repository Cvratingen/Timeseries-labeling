from setuptools import setup, find_packages

setup(
    name='timeseries_labeler',
    version='0.1',
    description='A tool for labeling time series data',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'matplotlib'
    ],
)
