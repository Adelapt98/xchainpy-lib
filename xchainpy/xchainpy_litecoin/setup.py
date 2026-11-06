from setuptools import setup , find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='xchainpy_litecoin',
    packages=find_packages(),
    version='0.2.1',
    license='MIT',
    description='Litecoin Module for XChainPy Clients',
    author='THORChain',
    author_email='',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/xchainjs/xchainpy-lib/tree/main/xchainpy/xchainpy_litecoin',
    keywords=["THORChain", "XChainpy","xchainpy_litecoin"],
    install_requires=['bitcoinlib>=0.7,<1', 'httpx>=0.27,<1', 'xchainpy_client>=0.1.6', 'xchainpy_crypto>=0.1.7', 'xchainpy_util>=0.1.8', 'bip_utils>=2.12,<3'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python'
    ],
)
