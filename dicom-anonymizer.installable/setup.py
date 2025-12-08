from setuptools import setup

setup(
    name="dicom-anonymizer",
    version="1.0.0",
    py_modules=["dicom-anonymizer"],
    install_requires=[
        "pydicom"
    ],
    entry_points={
        "console_scripts": [
            "anonymize-dicom=anonymize-dicom:main"
        ]
    }
)
