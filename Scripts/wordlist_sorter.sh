#!/bin/bash

# Wordlist sorter to parse words from multiple files and sort it to remove duplicates


echo "Please enter a file path, Dont forget to add * at end to select everyfile"
echo "Example files path: /home/exampleuser/wordlistfolder/*"
read FILES
you entered: $FILES


echo "Reading files from $FILES directory"
wc -w $FILES

while true; do
    read -p "Do you wish to sort these files" yn
    case $yn in
        [yes]* ) sort $FILES | uniq > newwordlist.txt; break;;
        [no]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
