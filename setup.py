from setuptools import setup, find_packages
from PyMemDump.utils.constants import __VERSION__, __AUTHOR__, __EMAIL__

setup(
    name="PyMemDump",
    version=__VERSION__,
    packages=find_packages(),
    author=__AUTHOR__,
    author_email=__EMAIL__,
    description='A Python library for memory dumping',
    long_description=open('Readme.md','r',encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/Fuxuan-CN/PyMemDump",
    package_data={
        'PyMemDump': ['res/lang.json']
    },
    requires=[
        'rich',
        'psutil'
    ],  # 依赖
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
)
