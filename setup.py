import os.path

from setuptools import setup, find_packages


__version__ = open(os.path.join(os.path.dirname(__file__),
                                "markdown_tags/VERSION")).read().strip()

setup(name='markdown_tags',
      version=__version__,
      description="A small library for writing markdown with a tree structure of python objects that you can transform into a markdown snippet(string).",
      long_description=open("./README.md", "r").read(),
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Topic :: Internet",
          "Topic :: Software Development :: Libraries :: Python Modules"
      ],
      keywords='markdown tags',
      author='Roman A. Taycher',
      author_email='rtaycher1987@gmail.com',
      url='http://crouchofthewildtiger.com/',
      license='MIT License',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=["enum34"],
      tests_require=['pyquery']
)
