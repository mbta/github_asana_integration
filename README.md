# github-asana-integration
This code is run as an AWS lambda that acts as a webhook for Github Pull Request Events. It updates the location of Asana tasks on a sprint board when PRs are opened or merged. It requires the Asana ticket URL to be in the PR description. It also updates a custom field on Asana tasks called "GitHub PR" with the PR's URL, including when only the PR description is updated.

# Setup for local development
* `brew install python3`
* `pip install virtualenv`

In `app` dir,
  * `virtualenv -p python3 venv`
  * Whenever you want to develop, activate the virtual env via: `. venv/bin/activate`
  * Once activated `pip install -r requirements-dev.txt`
  * To update requirements for production
    * `rm -rf venv` (to start with a fresh venv without dev dependencies)
    * `virtualenv -p python3 venv`
    * `. venv/bin/activate`
    * `pip install -r requirements.txt`
    * `pip install <dep>` and `pip freeze > requirements.txt`

The project currently includes `autopep8` for formatting and `pylint` for linting.
  * `autopep -i handler.py`
  * `pylint handler.py`

# Deployment of new code

In the repo's base directory, run:

```bash
$ ./deploy.sh <lambda-function-name>
```

…where `<lambda-function-name>` corresponds to the name of the Lambda function in AWS. The deploy script requires the [AWS CLI](https://aws.amazon.com/cli/) to be installed.
