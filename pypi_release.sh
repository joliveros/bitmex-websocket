#!/usr/bin/env bash

OPTIND=1         # Reset in case getopts has been used previously in the shell.

USAGE="PyPi release script.
Usage: checkout [-u][-p]
    -u      pypi user
    -p      pypi password
"

while getopts "u:p:h?:" opt; do
    case $opt in
      u)  user=$OPTARG
          ;;
      p)  password=$OPTARG
          ;;
      h)  echo $USAGE
          exit 0 ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

if [ -z "$user" ]; then
    echo "PyPi user is required."
    exit 1
fi

if [ -z "$password" ]; then
    echo "PyPi password is required."
    exit 1
fi

upload_pypi() {
    rm -rf ./dist
    python ./setup.py clean
    python ./setup.py bdist_egg upload -r pypi
}

BRANCH=$(git rev-parse --abbrev-ref HEAD)

VERSION=$(python ./bump_version.py)

LAST_LOG=$(git log -1 --pretty=%B)

MESSAGE="build: bump patch due to build."

if [[ $LAST_LOG =~ $MESSAGE ]]; then
    echo "last commit was result of a build."
    exit 0
fi

git add . --all && git commit -m "$MESSAGE"
git tag $VERSION -m "$MESSAGE"

if [ \( $BRANCH == HEAD \) -o \( $BRANCH == master \) ]; then
    git push origin
    upload_pypi
fi
