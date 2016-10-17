# automated-apt-install
Install a set of packes reading from a input file
You need to build a file that contains a list of packages that you want to install.
You need then to pass as argument the file path as in this example

./inst_pkg_from_file.sh /home/luke/packages

if you want to install also some .deb package,just put it in the deb_pkgs folder(remember to create it!!).
At this moment the folder needs to be in the same directory of the script.
