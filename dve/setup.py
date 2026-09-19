from setuptools import find_packages, setup

setup(
    name="dve",
    version="0.1.0",
    description="DSM-DVE: Design Verification Engine",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "Flask==2.3.2",
        "celery==5.2.3",
        "redis==4.1.1",
        "docker==7.1.0",
        "mdg",
    ],
    entry_points={"console_scripts": ["dsm=dve.__main__:main"]},
    package_data={
        "dve": [
            "dve.ini",
            "templates/*.html",
            "static/*",
            "static/fonts/*",
            "static/img/*",
        ]
    },
    include_package_data=True,
)
