from distutils.command.clean import clean
from distutils import log
from setuptools import setup
import os

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
      name='simple_signer',
      version=__import__('simple_signer').__version__,
      description='Sign and certify PDF files on Linux with optional visual stamp using a .p12/.pfx certificate',
      long_description=long_description,
      long_description_content_type='text/markdown',
      install_requires=[i.strip() for i in open('requirements.txt').readlines()],
      license=__import__('simple_signer').__license__,
      author='Georg Sieber',
      keywords='python3 pdf sign certify certificate stamp',
      url=__import__('simple_signer').__website__,
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: End Users/Desktop',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
            'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
      ],
      packages=['simple_signer'],
      package_data={'simple_signer': ['lang/*.qm']},
      entry_points={
            'gui_scripts': [
                  'simple-signer = simple_signer.simple_signer:main',
            ],
      },
      platforms=['all'],
      #install_requires=[],
      #test_suite='tests',
)
