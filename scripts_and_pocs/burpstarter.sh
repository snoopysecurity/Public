#!/bin/bash 
launch=echo java -jar -Xmx3g `ls . | grep 'burpsuite_pro_v1.7.0' | sort -r | head -n 1` 
echo $launch &
firefox

