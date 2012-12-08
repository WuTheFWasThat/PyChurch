# SHELL SCRIPT + DIRECTIONS for setup on EC2

# Presumably, you have already executed the following:

# sudo yum -y install git
# git clone https://github.com/WuTheFWasThat/Church-interpreter.git

git config --global user.email "wuthefwasthat@gmail.com"
git config --global user.name "Jeff Wu"
git clone https://github.com/probcomp/ProbabilisticEngineTestSuite.git

sudo easy_install flask

sudo yum -y install mercurial
sudo yum -y install gcc
sudo yum -y install make

hg clone https://bitbucket.org/pypy/pypy

cd Church-interpreter/src/

MAKE_NEW_SERVER=true
if $MAKE_NEW_SERVER; then
vim ~/pypy/pypy/annotation/annrpython.py
# comment out line 180
python ../../pypy/pypy/translator/goal/translate.py socket_server.py
# maybe reduced traces
cp socket_server-c ec2-jeff-traces-server
fi

cd ~
screen

# At this point, run

# python server.py
