#!/usr/bin/env bash
cd documents
git add .
git commit -m '-'
git push origin master
rm ../db/news.db