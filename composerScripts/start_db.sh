#!/bin/bash
echo Starting DBVM
VBoxManage startvm DBVM --type headless
sleep 10
ssh -p 2222 music@localhost sudo systemctl start mysql
echo DBVM ready
