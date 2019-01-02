#!/bin/sh
# (c) 2018 Yoichi Tanibayashi

MYNAME=`basename $0`

##### functions
usage() {
    echo "${MYNAME} outfile pin1 [pin2 ..]"
}

print_button_file() {
    echo -n "${BUTTON_FILE}: "
    cat ${BUTTON_FILE}
}
##### main
if [ "$1" = "" ]; then
    usage
    exit 1
fi

BUTTON_FILE=$1
shift

if [ "$*" = "" ]; then
    usage
    exit 1
fi

GPIO_PIN=$*
    
if [ -e ${BUTTON_FILE} ]; then
    print_button_file
    rm -v ${BUTTON_FILE}
fi

val0=""
echo -n "pin: "
for pin in ${GPIO_PIN}; do
    echo -n "${pin} "
    gpio -g mode ${pin} input
    val=`gpio -g read ${pin}`
    val0="${val0} ${val}"
done
echo

val0=`echo ${val0} | sed 's/^ *//'`
echo "val0=${val0}"
len=`echo ${val0} | tr ' ' '\n' | wc -l`
echo "len=${len}"

while true; do
    if [ -e ${BUTTON_FILE} ]; then
	print_button_file
	exit 0
    fi
    
    for i in `seq ${len}`; do
	pin=`echo ${GPIO_PIN} | cut -d ' ' -f $i`
	val1=`echo ${val0} | cut -d ' ' -f $i`
	val=`gpio -g read ${pin}`
	if [ ${val1} -ne ${val} ]; then
	    echo "pin ${pin}: ${val1}->${val}  "
	    echo ${pin} > ${BUTTON_FILE}
	fi
    done
    #echo
    #sleep 1
done

