from setuptools import setup, find_packages

setup(
    name="django-email-confirmation",
    version="0.2.dev6",
    description="Simple email confirmation for the Django web framework.",
    long_description=open("docs/index.txt").read(),
    author="James Tauber",
    author_email="jtauber@jtauber.com",
    url="https://github.com/jtauber/django-email-confirmation",
    packages=find_packages(exclude=["devproject.devtest", "devproject"]),
    package_data = {
        "emailconfirmation": [
            "templates/emailconfirmation/*.txt"
        ],
        'emailconfirmation.tests': [
            'templates/emailconfirmation/*.html'
        ],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    test_suite='runtests.runtests',
)
