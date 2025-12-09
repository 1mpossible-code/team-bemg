#!/bin/bash
# This shell script deploys a new version to a server.

PROJ_DIR="team-bemg"
PA_USER="teamBemg"
PA_DOMAIN="teambemg.pythonanywhere.com"
# Absolute path to the virtualenv used by the web app
VENV_PATH="/home/${PA_USER}/team-bemg/.venv"
echo "Project dir = $PROJ_DIR"
echo "PA domain = $PA_DOMAIN"
echo "Virtual env = $VENV_PATH"

if [ -z "$DEMO_PA_PWD" ]
then
    echo "The PythonAnywhere password var (DEMO_PA_PWD) must be set in the env."
    exit 1
fi

echo "PA user = $PA_USER"
echo "PA password = $DEMO_PA_PWD"

echo "SSHing to PythonAnywhere."
sshpass -p "$DEMO_PA_PWD" ssh -o "StrictHostKeyChecking no" "$PA_USER@ssh.pythonanywhere.com" << EOF
    set -e
    cd "/home/${PA_USER}/${PROJ_DIR}"
    PA_USER="${PA_USER}" \
    PROJ_DIR="/home/${PA_USER}/${PROJ_DIR}" \
    VENV_PATH="${VENV_PATH}" \
    PA_DOMAIN="${PA_DOMAIN}" \
    ./rebuild.sh
EOF
