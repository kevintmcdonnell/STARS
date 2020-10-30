#!/bin/bash

yellow='\033[0;33m'
off='\033[0m'

installed=$(pip3 list 2>/dev/null)
for package in $(awk -F "==" '{print $1}' ./requirements.txt); do
    echo $installed | grep $package >/dev/null
    if [ $? -eq 1 ]; then
        echo -e "${yellow}[+]${off} Installing required package $package"
        pip3 install $(grep $package ./requirements.txt)
    fi
done