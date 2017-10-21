#!/bin/bash

# Copy conf file to use
sudo mv /etc/ffserver.conf /etc/ffserver.conf.original
sudo cp ffserver.conf /etc/ffserver.conf
# Start server
nohup ffserver &
# Stream at 30x to generate sdp data
ffmpeg -i nyan.mp4 -an -f rtp rtp://localhost:5554 > output
tail -n +2 output > test.sdp
rm output nohup.out
