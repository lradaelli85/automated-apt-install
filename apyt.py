#!/usr/bin/python
# -*- coding: utf-8 -*-.
import os
import sys
import subprocess
import re
import platform

def WhoAmI():
    if os.geteuid() != 0:
        print 'need root privilege'
        sys.exit(1)

def ReplyYN(message):
    reply = ""
    while reply != 'y' and reply != 'n':
        reply = str(raw_input(message + ' [y/n]'))
    return reply

def CheckPath(file_or_folder):
    if not os.path.exists(file_or_folder):
        print file_or_folder+' command not found'
        sys.exit(1)

def CheckLinuxVer():
    distro = platform.linux_distribution()
    return distro

def CheckLinuxArch():
    arch = platform.machine()
    return arch

def CheckArgs():
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
            pkgs = sys.argv[1]
    elif len(sys.argv) < 2 or len(sys.argv) > 2:
        print "wrong parameters used"
        print "usage: " + sys.argv[0] + " package_file_list"
        sys.exit(1)
    else:
        print "file not found"
        sys.exit(1)
    return pkgs

def CheckDupPkgs():
    pack = CheckArgs()
    no_duplicates = set()
    with open(pack, 'r') as f:
        sorted_file = f.readlines()
    f.closed
    for items in sorted(sorted_file):
        stritem = str(items).strip("\n")
        if re.match(r'\S', stritem) and not stritem.startswith('#'):
            if stritem in no_duplicates:
                print """duplicate package found please remove it and try again.
                       \rPackage duplicated: """ + stritem
                sys.exit(1)
            else:
                no_duplicates.add(stritem)
    print "no duplicated packeges found!"
    return sorted(no_duplicates)

def CheckIfInRepo(package):
    apt_cmd = '/usr/bin/apt-cache'
    DEVNULL = open(os.devnull, 'wb')
    IsInRepo = True
    CheckPath(apt_cmd)
    print "check if "+package+" is in repo....."
    try:
     ps = subprocess.Popen([apt_cmd, 'search', '-n' , '-q' , package],
                           stdout=subprocess.PIPE)
     output = subprocess.Popen(['awk', '($1=="'+package+'") {print}'],
                               stdin=ps.stdout ,stderr=DEVNULL,
                               stdout=subprocess.PIPE)
     output1 = subprocess.check_output(['wc','-l'], stdin=output.stdout)
     ps.wait()
     if int(output1) == 0:
        print package+" is not in repository.....skipping \n"
        IsInRepo = False
     elif int(output1) == 1:
        print package+" is in repository.......ok \n"
    except subprocess.CalledProcessError as grepexc:
       print "error code", grepexc.returncode, grepexc.output
    return IsInRepo

def CheckIfDebIsInstalled(package):
    IsInstalled = False
    DEVNULL = open(os.devnull, 'wb')
    dpkg_cmd = '/usr/bin/dpkg-query'
    print 'checking '+package+'...'
    try:
      cmd = subprocess.check_output([dpkg_cmd , '-W' ,
                      '-f=\'${Status} ${Version}\'\n', package ]
                      ,stderr=DEVNULL)
      DEVNULL.close()
      if 'not-installed' in str(cmd) or 'deinstall' in str(cmd):
          print package+' is not installed....ok\n'
      else:
          print package+' is installed....skipping\n'
          IsInstalled = True
    except subprocess.CalledProcessError:
    #this is the case when dpkg-query returns
    #dpkg-query: no packages found matching package
      print package+' is not installed....ok\n'
    return IsInstalled


def InstFromList():
    dpkg_cmd = '/usr/bin/dpkg-query'
    CheckPath(dpkg_cmd)
    packages_list = CheckDupPkgs()
    for p in packages_list:
         IsInst = CheckIfDebIsInstalled(p)
         if not IsInst:
             inrepo = CheckIfInRepo(p)
             if inrepo:
                 InstFromRepo(p)

def InstFromRepo(package):
    apt_cmd = '/usr/bin/apt-get'
    DEVNULL = open(os.devnull, 'wb')
    CheckPath(apt_cmd)
    try:
        cmd = subprocess.Popen([apt_cmd , 'install' , '--no-install-recommends'
                               , package ])
        cmd.wait()
    except:
        print "error connecting to repositories,check internet connectivity"
    print "\n"


def InstFromFile(package):
    dpkg_cmd = '/usr/bin/dpkg'
    CheckPath(dpkg_cmd)
    cmd = subprocess.call([dpkg_cmd , '-i' , package] )
    if cmd != 0:
        print "forcing dependencies installation"
        try:
            ps = subprocess.Popen(['apt-get' ,'--no-install-recommends',
                                   '-f', 'install'])
            ps.wait()
        except:
            print "error forcing dependencies installation"

def InstFromDebFolder():
    folder="deb_pkgs"
    r = ReplyYN('do you want to install packages from the '+folder+' folder?')
    if r == 'y' and os.path.exists(folder):
        debs = os.listdir(folder)
        if debs:
            for i in debs:
                if str(i).endswith('.deb'):
                    repl = ReplyYN('do you want to install '+i+' ?')
                    if repl == "y":
                        InstFromFile(folder+'/'+i)
        else:
            print "empty folder"

def AddRepo(repofile,repo):
    if os.path.exists(repofile):
        try:
            with open(repofile, 'r') as configfile:
                if repo in configfile.read():
                    print "repository already present"
                else:
                    try:
                        with open(repofile, 'ab') as configfile:
                            configfile.write(repo)
                    except:
                        print "error opening "+repofile+" in write-append mode"
        except:
            print "error opening "+repofile+" in read-only mode"
    else:
        try:
            with open(repofile, 'w') as configfile:
                configfile.write(repo)
        except:
            print "error creating "+repofile+" file"

def RunAptUdate():
    try:
        ps = subprocess.Popen(['apt-get','update'])
        ps.wait()
    except:
        print "error connecting to repositories,check internet connectivity"

def AddAptKey(keyserver,key):
    try:
        ps = subprocess.Popen(['apt-key','adv','--keyserver',
                               keyserver,'--recv-keys',key])
        ps.wait()
    except:
        print "error adding key"

def InstSpotify():
    #taken from https://www.spotify.com/it/download/linux/
    r = ReplyYN("Do you want to install spotify? ")
    if r == 'y':
        IsInst = CheckIfDebIsInstalled("spotify-client")
        if not IsInst:
            AddAptKey("hkp://keyserver.ubuntu.com:80",
                      "BBEBDCB318AD50EC6865090613B00F1FD2C19886")
            AddRepo("/etc/apt/sources.list.d/spotify.list",
                    "deb http://repository.spotify.com stable non-free")
            RunAptUdate()
            InstFromRepo("spotify-client")

def InstSkype():
    r = ReplyYN("Do you want to install skype? ")
    if r == 'y':
        IsInst = CheckIfDebIsInstalled("skypeforlinux")
        if not IsInst:
            req = "apt-transport-https"
            keyurl = "https://repo.skype.com/data/SKYPE-GPG-KEY"
            IsInst = CheckIfDebIsInstalled(req)
            if not IsInst:
                InstFromRepo(req)
            try:
                ps = subprocess.Popen(['wget','-qO-',keyurl],
                                      stdout=subprocess.PIPE)
                output = subprocess.check_output(['apt-key', 'add', '-'],
                                                 stdin=ps.stdout)
                ps.wait()
                AddRepo("/etc/apt/sources.list.d/skype-stable.list",
                    "deb [arch=amd64] https://repo.skype.com/deb stable main")
            except subprocess.CalledProcessError as grepexc:
                print "error code", grepexc.returncode, grepexc.output
            RunAptUdate()
            InstFromRepo("skypeforlinux")

def InstDropbox():
    r = ReplyYN("Do you want to install dropbox? ")
    if r == 'y':
        IsInst = CheckIfDebIsInstalled("dropbox")
        if not IsInst:
            AddAptKey("pgp.mit.edu","1C61A2656FB57B7E4DE0F4C1FC918B335044912E")
            linux_ver = CheckLinuxVer()
            distro = str(linux_ver[0]).lower()
            distro_ver = str(linux_ver[2]).lower()
            AddRepo("/etc/apt/sources.list.d/dropbox.list",
                 "deb http://linux.dropbox.com/"+distro+" "+distro_ver+" main" )
            RunAptUdate()
            InstFromRepo("dropbox")

def InstExtras():
    InstSpotify()
    InstSkype()
    InstDropbox()

if __name__ == "__main__":
    WhoAmI()
    linux_distro = CheckLinuxVer()
    if linux_distro[0] == "Ubuntu" or linux_distro[0] == "Debian":
        InstFromList()
        InstFromDebFolder()
        InstExtras()
    else:
        print "unsupported Linux distro.Works only with Debian/Ubuntu"
