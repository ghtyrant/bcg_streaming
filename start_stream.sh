#!/bin/bash

FFSERVER_IN=http://localhost:8090/feed1.ffm
STREAM_URL=$(python twitch_live_url.py imaqtpie | head -n 5 | tail -n 1)
echo $STREAM_URL

ffmpeg -i $STREAM_URL -strict -2 $FFSERVER_IN
