#!/bin/sh
#
#Script to export
#$1 e.g. ewing.py

data_str=`date +"%m%d"`
server_dir='/data1/sg_game/trunk/sgServer'
log_dir='/data1/sg_game/ServerLog'
for x in `ps xww | grep "$1" | cut -c1-5`
do
        if [ $x != $$ ]
        then
                kill $x 2>/dev/null
				echo "kill $x 2>/dev/null"
        fi
done

if [ -z $2 ]
then
	nohup python ${server_dir}/$1 1>>${log_dir}/$1.${data_str}.log 2>>${log_dir}/$1.${data_str}.error.log &
	chmod 777 ${log_dir}/$1.${data_str}.log
	chmod 777 ${log_dir}/$1.${data_str}.error.log
	echo "Run >>> nohup python ${server_dir}/$1 &"
fi
