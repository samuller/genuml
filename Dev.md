## Dev setup

### Setup virtualenv

[Install poetry](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions):

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

Install packages:

    poetry install

Activate virtual environment:

    poetry shell

### Run tests

    pytest --cov-report html --cov genuml --verbose

### Check code

    flake8
    mypy genuml/
