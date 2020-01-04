# kill -9 `ps aux |grep gunicorn |grep flask_app:app | awk '{ print $2 }'`
# kill -9 `ps aux |grep flask | awk '{ print $2 }'`

export FLASK_APP=flask_app #:app
export FLASK_DEBUG=true
export FLASK_ENV=development
python3 -m flask run --port=8048
