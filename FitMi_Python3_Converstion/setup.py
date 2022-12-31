from setuptools import find_packages, setup
setup(
    name='Puck',
    packages=find_packages(include=['Puck']),
    version='1.0.0',
    description='Library of FitMi Helper Classes',
    long_description='Library of FitMi Helper Classes. These classes help connect to the pucks, parse incoming data, and analyze the data for the main scripts.',
    author='Nabeel Chowdhury',
    author_email='nabeel.chowdhury@case.edu',
    install_requires=['Cython==0.29.32', 'hidapi==0.12.0.post2', 'matplotlib==3.6.2', 'numpy==1.23.4', 'pygame==2.1.2', 'scipy==1.9.3'],
)