#!/bin/bash
##Author: Luca Radaelli <lradaelli85@users.noreply.github.com>
#install a set of packages reading from a file

PKGS="$1"
if [ `id -u` -ne 0 ]
 then
   echo "ERROR: only root is allowed to run this script"
   exit 1;
fi
 if [ ! -f $PKGS ] || [ "$#" -ne 1 ]
   then
     echo "ERROR: no such file or directory found"
     echo "check if the file with packges exists"
     echo "USAGE: $0 packages_file"
     exit 1;
 fi

while read line
do
#skip lines starting wih # or a space
if [[ ! $line =~ ^#|$^ ]]
then
dpkg -l $line &> /dev/null
if [ "$?" -eq 0 ]
 then
   echo "package "$line" already installed"
   else
    apt install $line -y
fi
fi
done < $PKGS



