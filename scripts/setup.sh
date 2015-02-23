#!/bin/bash
sudo apt-get update

sudo apt-get install git python-dev python-pip python-virtualenv ntp gnuplot

pip install -U pip
hash -r

virtualenv --no-site-packages .venv
. .venv/bin/activate

pip install uwsgi Cython falcon gevent dnspython redis
