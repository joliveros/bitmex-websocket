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

if [ $BRANCH != master ]; then
    echo "you're not on master branch"
    exit 1
fi

VERSION=$(python ./bump_version.py)

LAST_LOG=$(git log -1 --pretty=%B)

MESSAGE="build: bump patch due to build."

if [[ $LAST_LOG =~ $MESSAGE ]]; then
    echo "last commit was result of a build."
    exit 0
fi

git add . && git commit -m "$MESSAGE"
#git tag $VERSION -m $MESSAGE


#    if test $(findstring build:,$(shell git log -1 --pretty=%B)); then \
#        echo "last commit was result of a build."; else \
#        make config; \
#        python -c "from bump_version import bump_patch; bump_patch()"; \
#        git add . && git commit -m "build: bump patch due to build."; \
#        git tag $$(eval cat .version) -m "build: bump patch due to build."; \
#        ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts; \
#        git push origin; \
#        make pypi_register; \
#    fi; \