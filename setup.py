from setuptools import setup, find_packages

def load_requirements(filepath: str = "requirements.txt") -> list[str]:
    try:
       with open(filepath, 'r') as f:
           return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []
    except Exception:
        return []

setup(
    name="PyMemDump",
    version="0.1.6",
    packages=find_packages(),
    author="Fuxuan-CN",
    author_email="fuxuan001@foxmail.com",
    description='A Python library for memory dumping',
    long_description=open('Readme.md','r',encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/Fuxuan-CN/PyMemDump",
    requires=load_requirements(),  # 依赖
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
