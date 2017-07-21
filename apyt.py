#!/usr/bin/python
# -*- coding: utf-8 -*-.
import os
import sys
import subprocess
import re
import platform
import shlex
import argparse

apt_cache = '/usr/bin/apt-cache'
dpkg_query = '/usr/bin/dpkg-query'
apt_get= '/usr/bin/apt-get'
dpkg = '/usr/bin/dpkg'
apt_key = '/usr/bin/apt-key'

def WhoAmI():
    if os.geteuid() != 0:
        print 'need root privilege'
        sys.exit(1)

def ReplyYN(message):
    reply = ""
    while reply != 'y' and reply != 'n':
        reply = str(raw_input('%s [y/n]' %message))
    return reply

def CheckPath(file_or_folder):
    if not os.path.exists(file_or_folder):
        print "%s not found" %file_or_folder
        sys.exit(1)
    else:
        return True

def CheckLinuxVer():
    distro = platform.linux_distribution()
    return distro

def CheckLinuxArch():
    arch = platform.machine()
    return arch

def CheckArgs():
    parser = argparse.ArgumentParser(description="""
                                  apyt - automagically install .deb packages""")
    parser.add_argument("-f", help="packages file", metavar="file" ,required=True)
    parser.add_argument("-d", help=".deb directory", metavar="dir" ,required=False)
    args = parser.parse_args()
    if args.f and CheckPath(args.f):
        if args.d and CheckPath(args.d):
            return args.f,args.d
        else:
            return args.f

def RunProcess(command):
    try:
        args = shlex.split(command)
        cmd = subprocess.Popen(args)
        cmd.wait()
    except subprocess.CalledProcessError as grepexc:
        cmd = "error code", grepexc.returncode, grepexc.output
    return cmd


def CheckProcessOutput(command):
    try:
        args = shlex.split(command)
        cmd = subprocess.check_output(args)
    except subprocess.CalledProcessError as grepexc:
        cmd = "error code", grepexc.returncode, grepexc.output
    return cmd

def CheckDupPkgs():
    pack = CheckArgs()
    if type(pack) is tuple:
        pack = pack[0]
    no_duplicates = set()
    with open(pack, 'r') as f:
        sorted_file = f.readlines()
    f.closed
    for items in sorted(sorted_file):
        stritem = str(items).strip("\n")
        if re.match(r'\S', stritem) and not stritem.startswith('#'):
            if stritem in no_duplicates:
                print """duplicate package found please remove it and try again.
                       \rPackage duplicated: """ ,stritem
                sys.exit(1)
            else:
                no_duplicates.add(stritem)
    return sorted(no_duplicates)

def CheckIfInRepo(package):
    IsInRepo = True
    print "check if %s is in repo....." %package
    try:
     DEVNULL = open(os.devnull, 'wb')
     ps = subprocess.Popen([apt_cache, 'search', '-n' , '-q' , package],
                           stdout=subprocess.PIPE)
     output = subprocess.Popen(['awk', '($1=="%s") {print}' %package],
                              stdin=ps.stdout ,stderr=DEVNULL,
                              stdout=subprocess.PIPE)
     output1 = subprocess.check_output(['wc','-l'], stdin=output.stdout)
     ps.wait()
     DEVNULL.close()
     if int(output1) == 0:
        print "%s is not in repository.....skipping \n" %package
        IsInRepo = False
     elif int(output1) == 1:
        print "%s is in repository.......ok \n" %package
    except subprocess.CalledProcessError as grepexc:
       print "error code", grepexc.returncode, grepexc.output
    return IsInRepo

def CheckIfDebIsInstalled(package):
    IsInstalled = False
    print 'checking if %s is already installed' %package
    cmd = CheckProcessOutput('%s -W -f=\'${Status} ${Version}\' %s' %(dpkg_query,package))
    if 'not-installed' in str(cmd) or 'deinstall' in str(cmd):
        print '%s is not installed....ok\n' %package
    elif 'install ok' in cmd:
        print '%s is already installed....skipping\n' %package
        IsInstalled = True
    else:
        print '%s is not installed....ok\n' %package
        IsInstalled = False
    return IsInstalled


def InstFromList():
    packages_list = CheckDupPkgs()
    for p in packages_list:
         IsInst = CheckIfDebIsInstalled(p)
         if not IsInst:
             inrepo = CheckIfInRepo(p)
             if inrepo:
                 InstFromRepo(p)

def InstFromRepo(package):
    RunProcess('%s install --no-install-recommends %s' %(apt_get,package))

def InstFromFile(package):
    cmd = RunProcess('dpkg -i %s' %package)
    if cmd.returncode != 0:
        print "forcing dependencies installation"
        RunProcess('%s --no-install-recommends -f install' %apt_get)


def InstFromDebFolder():
    f = CheckArgs()
    if type(f) is tuple:
        f = f[1]
        if f:
            r = ReplyYN('do you want to install packages from the %s folder?' %f)
            if r == 'y':
                debs = os.listdir(f)
                if debs:
                    for i in debs:
                        if str(i).endswith('.deb'):
                            repl = ReplyYN('do you want to install %s ?' %i)
                            if repl == "y":
                                InstFromFile('%s/%s' %(f,i))
                else:
                    print "empty folder"

def AddRepo(repofile,repo):
    if CheckPath(repofile):
        try:
            with open(repofile, 'r') as configfile:
                if repo in configfile.read():
                    print "repository already present"
                else:
                    try:
                        with open(repofile, 'ab') as configfile:
                            configfile.write(repo)
                    except:
                        print "error opening %s in write-append mode" %repofile
        except:
            print "error opening in read-only mode" %repofile
    else:
        try:
            with open(repofile, 'w') as configfile:
                configfile.write(repo)
        except:
            print "error creating %s file" %repofile

def AddAptKey(keyserver,key):
    RunProcess('%s adv --keyserver %s --recv-keys %s' % (apt_key,keyserver,key))

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
            RunProcess('apt-get update')
            InstFromRepo("spotify-client")

def InstSkype():
    r = ReplyYN("Do you want to install skype? ")
    if r == 'y':
        IsInst = CheckIfDebIsInstalled("skypeforlinux")
        if not IsInst:
            keyurl = "https://repo.skype.com/data/SKYPE-GPG-KEY"
            IsInst = CheckIfDebIsInstalled("apt-transport-https")
            if not IsInst:
                InstFromRepo("apt-transport-https")
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
            RunProcess('apt-get update')
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
                 "deb http://linux.dropbox.com/%s %s main" %(distro,distro_ver))
            RunProcess('apt-get update')
            InstFromRepo("dropbox")

def InstExtras():
    InstSpotify()
    InstSkype()
    InstDropbox()

if __name__ == "__main__":
    WhoAmI()
    linux_distro = CheckLinuxVer()
    if linux_distro[0] == "Ubuntu" or linux_distro[0] == "Debian":
        for i in apt_get,apt_cache,dpkg,dpkg_query,apt_key:
            CheckPath(i)
        InstFromList()
        InstFromDebFolder()
        InstExtras()
    else:
        print "unsupported Linux distro.Works only with Debian/Ubuntu"
