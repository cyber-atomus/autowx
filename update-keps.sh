#!/bin/bash
TLEDIR=/tmp

rm $TLEDIR/noaa.txt
wget -qr https://www.celestrak.com/NORAD/elements/noaa.txt -O $TLEDIR/noaa.txt

rm $TLEDIR/amateur.txt
wget -qr https://www.celestrak.com/NORAD/elements/amateur.txt -O $TLEDIR/amateur.txt

rm $TLEDIR/cubesat.txt
wget -qr https://www.celestrak.com/NORAD/elements/cubesat.txt -O $TLEDIR/cubesat.txt

rm $TLEDIR/weather.txt
wget -qr https://www.celestrak.com/NORAD/elements/weather.txt -O $TLEDIR/weather.txt

rm $TLEDIR/multi.txt
wget -qr http://www.pe0sat.vgnet.nl/kepler/mykepler.txt -O $TLEDIR/multi.txt

echo `date`
echo Updated