#!/bin/bash

mkdir results 2> /dev/null

for (( i = 0 ; i < 61 ; i++ )) ; do
  a=$(printf "%02d" $i)
  echo -n "$a: "
  line=$(head -n $((i+1)) names | tail -n 1)
  last=$(cut -f 1 -d ';' <<< $line)
  first=$(cut -f 2 -d ';' <<< $line)
  echo "$first $last"
  ./eid.py --first "$first" --last "$last" > results/$a
  sleep 10
done
