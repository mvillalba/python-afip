from distutils.core import setup
from setuptools import find_packages
import afip


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='afip',
    packages=find_packages(),
    version=afip.__version__,
    license='MIT',
    description="Python package to interact with some of Argentina's AFIP Web services.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Martín Raúl Villalba',
    author_email='martin@martinvillalba.com',
    url='https://github.com/mvillalba/python-afip',
    python_requires='>=3',
    install_requires=[
        'requests>=2.22.0',
        'zeep>=3.4.0',
        'M2Crypto>=0.35.2',
        'python-dateutil>=2.8.0',
    ],
    # entry_points={
    #     'console_scripts': [
    #         'afip=afip.__main__:main',
    #     ],
    # },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'
    ],
)