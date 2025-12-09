#!/bin/bash
# This runs on PythonAnywhere servers: fetches new code,
# installs needed packages, and restarts the server.

set -e

touch rebuild
echo "Rebuilding $PA_DOMAIN"

echo "Pulling code from master"
git pull origin master

VENV_ACTIVATE="${VENV_PATH}/bin/activate"
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "Virtualenv not found at $VENV_ACTIVATE"
    exit 1
fi

echo "Activate the virtual env at $VENV_PATH for user $PA_USER"
source "$VENV_ACTIVATE"

echo "Install packages"
pip install --upgrade -r requirements.txt

echo "Reloading the web app"
pa_reload_webapp.py "$PA_DOMAIN"

touch reboot
echo "Finished rebuild."
