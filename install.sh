#!/bin/sh -x
# (c) 2018 Yoichi Tanibayashi
#

MISAKI_FONT=OledText.py

BINDIR=${HOME}/bin
LOGDIR=${HOME}/tmp

PKGS="python3-dev python3-pip libfreetype6-dev build-essentail i2c-tools libjpeg-dev"

if [ ! -x ${MISAKI_FONT} ]; then
    echo "${MISAKI_FONT}: no such file"
    exit 1
fi

if [ ! -d ${BINDIR} ]; then
    mkdir ${BINDIR}
fi
if [ ! -d ${LOGDIR} ]; then
    mkdir ${LOGDIR}
fi

sudo apt install -y ${PKGS}
sudo pip3 install -r requirements.txt
cp -rv MisakiFont/font ${HOME}
cp ${MISAKI_FONT} ${BINDIR}
cp ipaddr.py ${BINDIR}
cp boot-*.sh ${BINDIR}
