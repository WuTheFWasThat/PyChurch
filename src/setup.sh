# SHELL SCRIPT FOR SETUP ON EC2

# Presumably, you have already executed the following:

# sudo yum -y install git
# git clone https://github.com/WuTheFWasThat/Church-interpreter.git

git clone https://github.com/probcomp/ProbabilisticEngineTestSuite.git

sudo easy_install flask

sudo yum -y install mercurial

hg clone https://bitbucket.org/pypy/pypy

cd Church-interpreter/src/

python ../../pypy/pypy/translator/goal/translate.py socket_server.py

# maybe reduced traces
cp socket_server-c ec2-jeff-traces-server

