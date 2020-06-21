from setuptools import setup, find_packages

setup(
    name='csv2sqllike',
    version='1.0.0',
    packages=find_packages(),
    include_package_date=False,
    install_requirement=[
        'csv',
        'pymysql'
    ]
    download_url='https://github.com/hoosiki/csv2sqlLike/blob/master/dist/csv2sqllike-1.0.0.tar.gz'
)
