#!/bin/sh

# Test1:
i=0
while [ $i -lt 1000 ]
do
  curl http://localhost:9090/fibonacci?number=$i >> log1000-licensing.txt
  i=`expr $i + 1`
  sleep 1s
done

# Test2:
# k=0
# while [ $k -lt 10 ]
# do
#   i=0
#   while [ $i -lt 20 ]
#   do
#     curl http://localhost:9090/fibonacci?number=$i >> log${k}-licensing.txt
#     i=`expr $i + 1`
#     sleep 1s
#   done
#   k=`expr $k + 1`
# done
