from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="frappe_customizations",
    version="0.0.1",
    description="Frappe framework customizations, patches, and fixtures",
    author="Frappe Accelerated",
    author_email="admin@frappe-accelerated.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
