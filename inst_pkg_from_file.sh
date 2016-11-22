#!/bin/bash
#Author: Luca Radaelli <lradaelli85@users.noreply.github.com>
#install a set of packages reading from a file
#It works for Debian/Ubuntu

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
function force_dep_inst (){
  local ret=$1
  if [ $ret -eq 1 ]
    then
     echo "forcing dependencies installation"
     apt-get --no-install-recommends -f install
 fi

}
function inst_a_deb(){
local R
local folder="deb_pkgs/"
R=$(check_reply "do you want to install deb packages?[y/n]")
if [ $R = "y" ] && [ -d $folder ]
 then
    if [ `find $folder -type f -iname "*.deb"` ]
     then
      for i in `ls $folder`
        do
         dpkg -i $folder$i
         force_dep_inst $?
       done
     else
       echo "folder is empty,skipping...."
    fi
fi
}

function check_ver(){
REL=`lsb_release -is`
ARCH=`uname -m`
}

function inst_extras(){
  check_ver
  R=$(check_reply "do you want to install Spotify?[y/n]")
if [ $R = "y" ]
 then
    #taken from https://www.spotify.com/it/download/linux/
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys BBEBDCB318AD50EC6865090613B00F1FD2C19886
    echo "deb http://repository.spotify.com stable non-free" | tee /etc/apt/sources.list.d/spotify.list
    apt-get update
    apt-get install --no-install-recommends spotify-client

fi
R=$(check_reply "do you want to install DropBox?[y/n]")
if [ $R = "y" ]
then
  DROPBOX="https://www.dropbox.com/download?plat=lnx.x86_64"
  if [ $ARCH = "i686" ]
  then
    DROPBOX="https://www.dropbox.com/download?plat=lnx.x86"
  fi

   read -p "for which user dropbox will be installed?  " USR
   if [ `getent passwd |grep $USR` ]
     then
       su - $USR -c "cd /home/$USR && wget -O - $DROPBOX | tar xzf - && /home/$USR/.dropbox-dist/dropboxd && exit"
     else
       echo "user does not exist,skipping installation"
  fi
fi



R=$(check_reply "do you want to install Skype?[y/n]")
if [ $R = "y" ]
 then
   if [ $REL = "Debian" ]
    then
       wget -O skype.deb "http://www.skype.com/go/getskype-linux-deb"
       if [ $ARCH = "x86_64" ] && [ `lsb_release -sc` = "jessie" ]
        then
          dpkg --add-architecture i386
          apt-get update
          #apt-get install libc6:i386 libqt4-dbus:i386 libqt4-network:i386 libqt4-xml:i386 libqtcore4:i386 libqtgui4:i386 libqtwebkit4:i386 libstdc++6:i386 libx11-6:i386 libxext6:i386 libxss1:i386 libxv1:i386 libssl1.0.0:i386 libpulse0:i386 libasound2-plugins:i386
          dpkg -i skype.deb
          force_dep_inst $?
      else
         dpkg -i skype.deb
         force_dep_inst $?
      fi
  elif [ $REL = "Ubuntu" ]
    then
      add-apt-repository "deb http://archive.canonical.com/ $(lsb_release -sc) partner"
      apt-get update && apt-get install skype
      apt-get clean
      add-apt-repository -r "deb http://archive.canonical.com/ $(lsb_release -sc) partner"
  fi
fi
}

function check_pack_in_repo(){
  skipped="skipped.txt"
  to_inst="pack_to_install.txt"
  cat /dev/null > $to_inst
  cat /dev/null > $skipped
  for p in `cat $PKGS |grep -Ev "^#|$^"`
   do
    if [ `apt-cache search --names-only $p |awk '($1=='\"$p\"') {print}' |wc -l` -eq 1 ]
     then
       echo "$p exists"
       echo $p >> pack_to_install.txt
     else
       echo "$p does not exists,skipping...."
       echo $p >> skipped.txt
   fi
 done
 if [ -s $skipped ]
    then
      echo "check $skipped for skipped packages"
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
    apt-get install --no-install-recommends $line -y
fi
fi
done < $1
rm $to_inst
#if [ `dpkg --print-foreign-architectures` = "i386" ]
#   then
#     dpkg --remove-architecture i386
#fi
}

#Main
WhoAmI
check_param $PKGS
check_dup
check_pack_in_repo $PKGS
inst_a_deb
check_ver
inst_extras
inst_pkgs $to_inst
