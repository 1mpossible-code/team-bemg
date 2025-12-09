# +++++++++++ FLASK +++++++++++

import sys
import os

from dotenv import load_dotenv

path = '/home/teamBemg/team-bemg'
if path not in sys.path:
    sys.path.append(path)

env_path = os.path.join(path, '.env')
load_dotenv(env_path)

from server.app import app as application  # noqa
