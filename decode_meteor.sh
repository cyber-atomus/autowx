#!/bin/bash
DIR=/opt/autowx/lrpt

xvfb-run wine $DIR/rgb.exe
xvfb-run wine $DIR/mono.exe
