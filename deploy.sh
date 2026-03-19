#!/bin/bash
set -euo pipefail
cd /home/sanderburuma/memorization

git fetch origin master
git reset --hard origin/master
source venv/bin/activate
pip install -q -r requirements.txt
python manage.py migrate --no-input
python manage.py collectstatic --no-input
sudo systemctl restart memorization
echo "Deploy complete"
