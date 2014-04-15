#!/bin/bash
## Simple shell script that reboots the bot if it crashes - NOT TESTED
until python magictcg_bot.py; do
	echo "CRASH" >&2
	sleep 1
done
