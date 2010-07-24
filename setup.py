from setuptools import setup, find_packages

setup(
    name="tahoestorage",
    version="0.1",
    author="Anders Pearson",
    author_email="anders@columbia.edu",
    url="http://wiki.ccnmtl.columbia.edu/",
    description="Django FileStorage adaptor for Tahoe-LAFS",
    long_description="let's you use a Tahoe grid for filestorage for your django models",
    install_requires = [],
    scripts = [],
    license = "BSD",
    platforms = ["any"],
    zip_safe=False,
    package_data = {'' : ['*.*']},
    packages=['tahoestorage'],
    test_suite='',
    )
