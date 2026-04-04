#!/usr/bin/bash
filename="$1"
while read -r line
do
    name="$line"
    echo
    echo "Sending PUT request to $name"
	echo
    curl -IXOPTIONS "$name"


done < "$filename"




