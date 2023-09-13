#!/bin/bash

set -e
cd /opt/Star-burger/star-burger
git pull
pip install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
systemctl daemon-reload
curl -H "X-Rollbar-Access-Token: $(cat .env | grep ROLLBAR_ACCESS_TOKEN| cut -d "=" -f 2)" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "development", "revision": "'"$(git rev-parse HEAD)"'", "rollbar_name": "rostwik", "local_username": "rostwik", "status": "succeeded"}'
echo "Деплой успешно завершен"
