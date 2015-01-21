uwsgi --http :9090 --gevent 1000 --wsgi-file app.py --callable app
