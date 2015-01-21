uwsgi --http :9090 --gevent 2 --wsgi-file app.py --callable app
