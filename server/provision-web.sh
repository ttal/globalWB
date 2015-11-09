#!/usr/bin/env bash

sudo apt-get install -y python-software-properties
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections
sudo apt-get install -y oracle-java8-installer
# sudo update-alternatives --config java

sudo sh -c 'echo JAVA_HOME=\"/usr/lib/jvm/java-8-oracle\" >> /etc/environment'
sudo sh -c 'echo ODIN_HOME=\"/home/vagrant/odin\" >> /etc/environment'
sudo sh -c 'echo ODIN_ENV=\"dev\" >> /etc/environment'
source /etc/environment

sudo apt-get install -y git

sudo apt-get install -y curl
curl -sL https://deb.nodesource.com/setup | sudo bash -
sudo apt-get install -y nodejs

sudo npm -g install npm@2.10.1
sudo npm cache clean

sudo npm install -g yo@1.4.6
sudo npm install -g bower
sudo npm install -g grunt-cli
sudo npm install -g http-server

sudo apt-get -y install python-matplotlib
sudo apt-get -y install python-tk