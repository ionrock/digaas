#!/bin/bash
sudo apt-get -y update

sudo apt-get -y install git python-dev python-pip python-virtualenv ntp gnuplot

pip install -U pip
hash -r

git clone https://github.com/pglass/digaas.git
cd digaas
virtualenv --no-site-packages .venv
. .venv/bin/activate

pip install uwsgi Cython falcon gevent dnspython redis

echo "digaas setup complete."
echo "To configure digaas:"
echo "  - copy digaas_config.py.sample to digaas_config.py"
echo "  - update digaas_config.py "
echo "To start digaas:"
echo "  . .venv/bin/activate"
echo "  ./bin/digaas.sh &"
echo "REMEMBER TO SYNC TO NETWORK TIME"
