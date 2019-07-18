#!/bin/bash

# Lambda function deploy script
# Builds function dependencies, creates a zip archive, and publishes it to
# Lambda via the AWS CLI.
#
# Usage:
#   deploy.sh <lambda-function-name>
#
# Requirements:
#   AWS CLI
#   Python 3
#   Virtualenv

# 3-finger claw, for error handling
shout() { echo "$0: $*" >&2; }
die() { shout "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }

function_name="${1:?Usage: $0 <function-name>}"
function_config_ini="config/${function_name}.ini"
canonical_config_ini="config.ini"
tmpdir="$(mktemp -d "/tmp/lambda-${function_name}-XXXXXX")"
version="${function_name}-$(git rev-parse --short HEAD)"
zipfile="${tmpdir}/${version}.zip"

check_program() {
    # confirm the existence of the given program on the system
    command -v "${1}" > /dev/null \
     || die "Error: Could not find required dependency '${1}'."
}

clean_env() {
    # get out of and remove any existing virtualenv
    if [ "$VIRTUAL_ENV" != "" ]; then
        deactivate
    fi
    if [ -d "app/venv" ]; then
        echo "Cleaning up existing virtualenv..."
        rm -rf app/venv
    fi
}

check_program aws
check_program python3
check_program virtualenv

# confirm that we're at the root of the repo
if [ "$( cd "$(dirname "$0")" ; pwd -P )" != "$(pwd)" ]; then
    die "This program must be run from the root of the repo."
fi

# cd to the app directory for virtualenv setup
try cd app

# confirm there's a config file for the function we're deploying
if [ ! -f "${function_config_ini}" ]; then
    die "Error: This script requires a config file at app/${function_config_ini}."
fi

# set up the virtualenv and install function requirements
clean_env
echo "Setting up virtualenv..."
try virtualenv -p python3 venv
# shellcheck disable=SC1091
. venv/bin/activate
echo "Installing requirements..."
try pip install -r requirements.txt
deactivate

# add the handler and its dependencies to the zipfile
echo "Packaging dependencies..."
(try cd venv/lib/python3.7/site-packages && try zip -r9 "${zipfile}" ./*)
try zip -g "${zipfile}" handler.py

# add the config file
try cp "${function_config_ini}" "${tmpdir}/${canonical_config_ini}"
(try cd "${tmpdir}" && try zip -g "${zipfile}" "${canonical_config_ini}")

# upload the zipfile to Lambda
echo "Uploading $(basename "${zipfile}") to Lambda function ${function_name}..."
try aws lambda update-function-code \
    --function-name "${function_name}" \
    --zip-file "fileb://${zipfile}"

# clean up
clean_env
rm -rf "${tmpdir}"

echo "Success."
