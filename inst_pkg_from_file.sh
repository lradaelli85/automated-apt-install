#!/bin/bash
##Author: Luca Radaelli <lradaelli85@users.noreply.github.com>
#install a set of packages reading from a file

PKGS="$1"

function WhoAmI (){
if [ `id -u` -ne 0 ]
 then
   echo "ERROR: only root is allowed to run this script"
   exit 1;
fi
}

function check_reply(){
  local var
  local print_message=$1
  until [ ! -z $var ] && ([ $var = "y" ] || [ $var = "n" ])
   do
    read -p "$print_message  " var
   done
   echo $var
}

function inst_a_deb(){
local R
local folder="deb_pkgs/"
R=$(check_reply "do you want to install deb packages?[y/n]do you want to install deb packages?[y/n]")
if [ $R = "y" ] && [ -d $folder ]
 then
    if [ `find deb_pkgs/ -iname *.deb` ]
     then
        #echo "install a deb"
       apt install $folder*.deb -y
     else
       echo "folder is empty,skipping...."
    fi
fi
R=$(check_reply "do you want to install Spotify?[y/n]")
if [ $R = "y" ]
 then
    #taken from https://www.spotify.com/it/download/linux/
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys BBEBDCB318AD50EC6865090613B00F1FD2C19886
    echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
    apt-get update
    apt-get install spotify-client
fi

}

function check_param (){

local pkgs_number

 if [ ! -f $PKGS ] || [ "$#" -ne 1 ]
   then
     echo "ERROR: no such file or directory found"
     echo "check if the file with packges exists"
     echo "USAGE: $0 packages_file"
     exit 1;
 fi

pkgs_number=`cat $PKGS |grep -vE "^#|$^" |wc -l`
echo "$pkgs_number packages found"
if [ $pkgs_number -eq 0 ]
 then
  echo "no packages found or empty file"
  exit 1;
fi
}

function check_dup(){
local DUPS
DUPS=`sort $PKGS |uniq -d`
if [ ! -z "$DUPS" ]
 then
  echo "there are some duplicated packages"
  echo "$DUPS"
  exit 1;
   else
     echo "no duplicated packages found"
fi
}

function inst_pkgs(){
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
}

#Main
WhoAmI
check_param $PKGS
inst_a_deb
check_dup
inst_pkgs
