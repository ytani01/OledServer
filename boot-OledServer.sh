#!/bin/sh
# (c) 2018 Yoichi Tanibayashi
#
MYNAME=`basename $0`

BINDIR=${HOME}/bin
LOGDIR=${HOME}/tmp
ENVDIR=${HOME}/env
ENVBIN=${ENVDIR}/bin

MISAKI_FONT=${BINDIR}/MisakiFont.py
if [ -x ${ENVBIN}/MisakiFont.py ]; then
    MISAKI_FONT=${ENVBIN}/MisakiFont.py
fi

LOGFILE=${LOGDIR}/${MYNAME}.log

if [ ! -d ${LOGDIR} ]; then
    mkdir ${LOGDIR}
fi

if [ -f ${ENVBIN}/activate ]; then
    . ${ENVBIN}/activate
fi
cd ${BINDIR}
date > ${LOGFILE} 2>&1
${MISAKI_FONT} >> ${LOGFILE} 2>&1
