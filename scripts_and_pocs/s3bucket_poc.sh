#!/bin/bash
aws s3api put-object-acl --bucket $1 --key $2 --grant-full-control emailaddress=$3 --grant-write uri=http://acs.amazonaws.com/groups/global/AuthenticatedUsers
aws s3api get-object-acl --bucket $1 --key $2