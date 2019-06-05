# Work in progress
This app is intended to be a AWS lambda that will act as a webhook for Github Pull Request Events and update Asana tasks accordingly.

# Basic setup for local development
* `brew install python3`
* `brew install virtualenv`
* In this `app` dir, 
  * `virtualenv -p python3 venv`
  * Whenever you want to develop, activate the virtual env via: `. venv/bin/activate`
  * Once activated `pip install -r requirements-dev.txt`
  * To update requirements for production 
    * `rm -rf venv` (to start with a fresh venv without dev dependencies)
    * `virtualenv -p python3 venv`
    * `. venv/bin/activate`
    * `pip install <dep>` and `pip freeze > requirements.txt`

The project currently includes `autopep8` for formatting and `pylint` for linting.

# Basic deployment of new code
* In this `app` dir:
  * Add the dependencies
    *  `rm -rf venv`
    *  `virtualenv -p python3 venv`
    *  `. venv/bin/activate`
    *  `pip install requirements.txt`
    *  `deactivate`
    *  `cd venv/lib/python3.7/site-packages`
    *  `zip -r9 ../../../../function.zip .`
  * Add the handler
    *  `cd ../../../../` back to `app`
    *  `zip -g function.zip handler.py`
      And then upload the zip in the AWS Lambda console or via the AWS CLI.
