#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <twitch_channel>"
    exit 1
fi

echo "*** sDream Catcher v0.1 ***"

FFSERVER_IN=http://localhost:8090/feed1.ffm
echo "Resolving Twitch stream URL ..."
STREAM_URL=$(python twitch_live_url.py $1)

if [[ $? -ne 0 ]]; then
    echo "Error resolving Twitch stream URL for '$1'!"
    exit -1
fi

STREAM_URL=$(python twitch_live_url.py $1 | head -n 5 | tail -n 1)

echo "Streaming Twitch stream '$STREAM_URL' to '$FFSERVER_IN' ..."

echo
echo
echo
echo "-----------------------------------------------------------------------------------------------"
ffmpeg -i $STREAM_URL $FFSERVER_IN
