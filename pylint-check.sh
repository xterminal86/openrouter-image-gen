#!/bin/bash

source venv/bin/activate || exit 1

pylint -h &> /dev/null

linterExists=$?

if [ ${linterExists} -ne 0 ]; then
  echo "pylint not found!"
  exit
fi

find . -iname "*.py" -not -path "./venv/*" |
xargs pylint -E

if [ $? -eq 0 ]; then
  echo "Looks OK"
fi

deactivate

