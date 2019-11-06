#!/bin/zsh

LOG_FILE=$1
for row in floor 1 2 3 4 5
do
	COUNT=$(awk -v pattern="tile row $row" '$0 ~ pattern { count++ }END{print count}' $LOG_FILE)
        echo "$row: $COUNT"
done

echo "Valid"
awk '/Valid / {count++}END{print count}' $LOG_FILE
echo "Invalid"
awk '/Invalid / {count++}END{print count}' $LOG_FILE
echo "Games"
awk '/Earned a total of reward / {count++}END{print count}' $LOG_FILE
