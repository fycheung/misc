#!/bin/sh

#使用方式 sgserver.sh gateway.py  [start|stop|restart]

# Source function library.
. /etc/rc.d/init.d/functions

# Need to init
sid=1
pyfile=$1 #python文件
rootpath=/data1/sg_game/trunk/sgServer
log_dir=/data1/sg_game/ServerLog

port = $2
echo "port=$port"
# Shell start
pid=0
data_str=`date +"%m%d"`
len=$(expr length "$pyfile")-3
basename=${pyfile:0:len} #文件名  去掉扩展名.py

if [ ! -d "$log_dir" ]; then 
	mkdir "$log_dir" 
fi 

pid_file=$rootpath/pid/$basename.pid  #要跟下面要运行的py文件名对应 
if [ ! -f "$pid_file" ]; then 
	echo 0 > $pid_file
fi 
echo "pid_file: $pid_file"

stop()
{
  getpid
  if [ $pid -ne 0 ] ; then
        kill -10 $pid
        sleep 1
        echo "kill exist process sgserver's daemon, pid:$pid."
		#echo 0 > $pid_file #已写到python里
  else
        echo "no daemon exist"
  fi
}
start()
{
	getpid
	PROCESS_NUM=`ps -ef | grep "$pid" | grep -v "grep" | wc -l` 
	if [ $PROCESS_NUM -eq 1 ]; then
        echo "sgserver's daemon already start and alive, pyfile:$1 , pid:$pid."
	else
        nohup /usr/local/bin/python $rootpath/$pyfile 1>>$log_dir/s$sid.$data_str.$basename.log 2>>$log_dir/s$sid.$data_str.$basename.error.log &
		#如果不要输出日志 1>>/dev/null   日志文件例子:  s1.0723.gateway.log, s1.0723.gateway.error.log
		chmod 777 $log_dir/s$sid.$data_str.$basename.log
		chmod 777 $log_dir/s$sid.$data_str.$basename.error.log
 		sleep 1
		getpid
		echo "sgserver's daemon  pyfile:$1 , new pid: $pid start"
		if [ $pid -eq 0 ] ; then
			echo "Start Error: nohup /usr/local/bin/python $rootpath/$pyfile 1>>$log_dir/s$sid.$data_str.$basename.log 2>>$log_dir/s$sid.$data_str.$basename.error.log &"
		fi
	fi
}
restart()
{
	stop
	sleep 8
	start
}
reload()
{
	getpid
	if [ $pid -ne 0 ] ; then
        kill -12 $pid
        sleep 1
        echo "sgserver's daemon, pyfile:$1 ,pid:$pid, python module reload()"
	else
		echo "no daemon exist"
	fi

}


check() #暂未使用
{
	getpid
	PROCESS_NUM=`ps -ef | grep "$pid" | grep -v "grep" | wc -l` 
	if [ $PROCESS_NUM -eq 1 ];
	then
		echo "print $pid alive..."
	else
		echo "$pid notexist need start server"
		start
	fi
}
getpid()
{
        pid=$(cat $pid_file)
}


if [ $2 = "start" ] ; then
        start
elif [ $2 = "restart" ] ; then
        restart
elif [ $2 = "stop" ] ; then
        stop
elif [ $2 = "check" ] ; then
        check
elif [ $2 = "reload" ] ; then
        reload
fi
