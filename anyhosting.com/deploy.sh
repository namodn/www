#!/bin/sh
rsync --delete-after -av ./ /var/www/staging.anyhosting.com/ --exclude=logs/ --exclude=htdocs/webalizer --exclude=htdocs/robots.txt --exclude=htdocs/blog --exclude=htdocs/clients
