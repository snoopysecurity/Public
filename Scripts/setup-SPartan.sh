#!/bin/bash

echo 'This script installs SPartan, a Frontpage and Sharepoint fingerprinting and attack tool created by Sensepost'

echo 'Installing Python2.6'
echo '------------------------------------'
add-apt-repository ppa:fkrull/deadsnakes
apt-get update -y
apt-get install python2.6 python2.6-dev -y

echo 'Installing Pip2.6'
echo '------------------------------------'
wget https://bootstrap.pypa.io/get-pip.py --no-check-certificate
chmod +x get-pip.py
python2.6 get-pip.py

echo 'Checking if Git is installed'
echo '------------------------------------'
PKG_OK=$(dpkg-query -W --showformat='${Status}\n' git|grep "install ok installed")
echo Checking for somelib: $PKG_OK
if [ "" == "$PKG_OK" ]; then
  echo "No somelib. Setting up somelib."
  sudo apt-get --force-yes --yes git
fi


echo 'Downloading SPartan'
echo '------------------------------------'
git clone https://github.com/sensepost/SPartan.git;
cd SPartan
pip2.6 install -r requirements.txt
python2.6 SPartan.py -v
echo 'Done! :)'
