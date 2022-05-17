from setuptools import setup, find_packages

setup(
	name='api_client',
	version='2.0.0',
	packages=find_packages(exclude=['tests', 'assets', 'tmp']),
	install_requires=[
		"requests"
	]
)
