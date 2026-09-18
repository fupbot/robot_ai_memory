from setuptools import find_packages, setup

package_name = "okf_robotics_mcp"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test", "test.*"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools", "mcp"],
    zip_safe=True,
    maintainer="Ugalde Pereira",
    maintainer_email="ugaldepereira@gmail.com",
    description="MCP server exposing read-only query/search over an OKF robotics bundle.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "okf_robotics_mcp = okf_robotics_mcp.server:main",
        ],
    },
)
