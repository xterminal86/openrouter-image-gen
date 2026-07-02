#!/bin/bash

read -p "This will delete all .txt files in raw/ and errors/ folders.
Do you want to continue? (y/n): " answer

case $answer in
  [Yy]* )
    ls raw/*.txt | grep -v README | xargs rm -f
    ls errors/*.txt | grep -v README | xargs rm -f
    echo "Done!"
    ;;

  [Nn]* ) echo "Exiting.";
    exit
    ;;

  * )
    echo "Please answer yes or no."
    ;;
esac
