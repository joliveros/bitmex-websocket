import semver
from os.path import realpath

def bump_patch():
    version_file = open(realpath('./.version'), 'r+')
    version = semver.bump_patch(version_file.read().rstrip())

    version_file.seek(0)

    version_file.write(version)

    version_file.truncate()
    version_file.close()
