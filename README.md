# About
This application is a simple application to use for learning about testing APIs. It has some bugs built into it and there are some challenges that you can use to try out your testing skills.

# Install and Setup

## Using Gitpod
The easiest way to run this is in gitpod. This should have all the dependencies setup for your automatically. You can do that with the following steps:

1.	First of all, you will need a GitHub account. If you don’t yet have one you can sign up at https://github.com.
2.	Once you have that account, navigate to https://gitpod.io/#https://github.com/djwester/todo-list-testing in your browser
3.	Click to Continue with GitHub.
4.	You can accept the default workspace settings and continue.
5.	Once it has finished loading, go to the terminal and type in the command `make run-dev` and hit enter.
6.	The service should start and you should see a toast message with a few options. Click on the **Make Public** option.
7.	Click on the Ports tab and you can see the public URL of the test site available to copy.

>Note that GitPod will shut this site down after a few minutes of inactivity, so if you haven’t been using it for a while and you get an error when making API calls, you may have to come back and repeat these steps to restart the site. Also every time you restart the site it will have a slightly different URL so don’t forget to update the URL of any API calls pointing at this site. 


## Running Locally
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

Once everything is installed, you can create the environment file by calling:

```bash
cp .envrc.example .envrc
```

You will need `direnv` to set your environment. If you don't yet have it installed, follow the instructions [here](https://direnv.net/docs/installation.html) to install it.

Call `direnv allow` to set the environment variables, and should now be ready to run the application.

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

