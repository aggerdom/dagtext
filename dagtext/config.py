import os
import sys
from pathlib import Path
from configparser import ConfigParser

parser = ConfigParser()
parser.add_section("DefaultLocations")

if sys.platform == "win32":
    savedir = Path(os.environ["USERPROFILE"], ".dagtext")
    if not savedir.exists():
        savedir.mkdir()
else:
    raise NotImplementedError
