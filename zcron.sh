#!/bin/bash
source ~/.bashrc
py=`which python`
echo $py

mkdir -p backtests
mkdir -p data
mkdir -p data
mkdir -p output
mkdir -p logs
mkdir -p output/nbs/
mkdir -p output/kline/

# download data
# bash download.sh

day0=`date +"%Y-%m-%d"`
# day0='2016-08-09'
echo $day0

###--- DOWNLOAD DT_BOARD
rsync -uhavzm --stats --progress himalayas@139.129.99.51:/home/himalayas/apps2/qts/pytrade2/data/dtboard.csv ./data/

###--- 计算龙虎榜
$py indicator.py

### link缠中说缠
unlink data/czsc
ln -s /data/lihz/data/$day0/shape1 data/czsc

###--- TRAIN ---
$py pp_selstock.py -m 'train' -s 2017-01-01 -d $day0 -t triangle -p day
# $py pp_selstock.py -m 'train' -s 2017-01-01 -d $day0 -t triangle -p week
# $py pp_selstock.py -m 'train' -s 2017-01-01 -d $day0 -t triangle -p month
# $py pp_selstock.py -m 'train' -s 2017-01-01 -d $day0 -t triangle -p 60min
# $py pp_selstock.py -m 'train' -s 2017-01-01 -d $day0 -t triangle -p 30min

mkdir -p ./data/dayk/$day0/
python pp_utils.py -m line -d $day0
touch ./tmp/$day0.done
tar -czvf ./tmp/$day0."dayk".tar.gz ./data/dayk/$day0/*
rsync -uhavzm --stats --progress tmp/$day0.dayk.tar.gz  himalayas@139.129.99.51:/data/from_offline/kline_shape/
rsync -uhavzm --stats --progress tmp/$day0.done  himalayas@139.129.99.51:/data/from_offline/kline_shape/

rsync -uhavzm --stats --progress tmp/$day0.dayk.tar.gz  himalayas@192.168.200.20:/data/from_offline/kline_shape/
rsync -uhavzm --stats --progress tmp/$day0.done  himalayas@192.168.200.20:/data/from_offline/kline_shape/

nohup $py pp_selstock.py -m 'mock' -s 2017-01-03 -d $day0 -t triangle 1>logs/$day0.triangle.log 2>&1 &

scp data/dayk/* himalayas@192.168.200.11:/data/server/nfsclient/stock/dayk/ 1>upload.log 2>&1
