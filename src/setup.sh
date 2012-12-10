# SHELL SCRIPT + DIRECTIONS for setup on EC2

sudo yum -y install git
# clone this repo!
git clone https://github.com/WuTheFWasThat/Church-interpreter.git

sudo yum -y install mercurial
sudo yum -y install gcc
sudo yum -y install make

git config --global user.email "wuthefwasthat@gmail.com"
git config --global user.name "Jeff Wu"

sudo easy_install flask
sudo easy_install pip



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

################################################################################
# To run the lda stuff
################################################################################

sudo yum -y install atlas-devel
sudo yum install lapack
#sudo pip install scipy


#sudo easy_install -U distribute
#sudo yum -y install python-devel

#sudo pip install -U numpy
git clone git://github.com/numpy/numpy.git numpy
cd numpy
sudo python setup.py install

sudo pip install -U pyyaml nltk

sudo yum -y install python-matplotlib

git clone https://github.com/probcomp/ProbabilisticEngineTestSuite.git
