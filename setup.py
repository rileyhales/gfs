from setuptools import setup, find_namespace_packages
from tethys_apps.app_installation import find_resource_files

# -- Apps Definition -- #
app_package = 'gfs'
release_package = 'tethysapp-' + app_package

# -- Python Dependencies -- #
dependencies = []

# -- Get Resource File -- #
resource_files = find_resource_files('tethysapp/' + app_package + '/templates', 'tethysapp/' + app_package)
resource_files += find_resource_files('tethysapp/' + app_package + '/public', 'tethysapp/' + app_package)

setup(
    name=release_package,
    version='4',
    description='Visualizes GFS data through maps and charts',
    long_description='',
    keywords='GFS',
    author='Riley Hales',
    author_email='',
    url='',
    license='',
    packages=find_namespace_packages(),
    package_data={'': resource_files},
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
)
