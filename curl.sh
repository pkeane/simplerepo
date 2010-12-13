#!/bin/sh

PASSWORD=$1

curl -f -s --output myAuthFile.txt -d Email=pjkeane@gmail.com -d Passwd=$PASSWORD -d accountType=GOOGLE -d service=ah -d source=simplerepo https://www.google.com/accounts/ClientLogin

