# About
This application is a simple application to use for learning about testing APIs. It has some bugs built into it and there are some challenges that you can use to try out your testing skills.

# Install and Setup
You will need python 3.11 to run this application. You can check what version of python you have by going to the command shell (search for "terminal" in your applications) and calling 
```bash
python -V
```
Note that on older Macs you that come with python 2 installed the `python` command will point to python 2. You should also try running `python3 -V` to see if you have python 3 installed.

If you do not have version 3.11, you will need to install it.

### Mac OS
You can install python on a Mac using the `homebrew` package manager. If you do not yet have homebrew installed (you can check by running `which homebrew`), run the following command

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

To install python run this command:
```bash
brew install python@3.11
```

### Windows
To install the latest version of python on Windows, go to the [Windows downloads](https://www.python.org/downloads/windows/) page on python.org. Download the latest release and run the installer.

## Setup
With python installed, you are ready to setup this application. It uses [poetry](https://python-poetry.org/docs/) to for dependency management. You can install poetry with the following command:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Once you have it installed, you can use it to install all the other package dependencies.

```bash
poetry install
```

Once everything is installed, you can create the 
## Running the app locally
In order to run this app locally call this command:

```bash
poetry run uvicorn main:app --reload
```

Alternatively, you can run it with the make command:

```bash
make run-dev
```

You can then access the application at http://127.0.0.1:8000

You can see documentation for the API at http://127.0.0.1:8000/docs

