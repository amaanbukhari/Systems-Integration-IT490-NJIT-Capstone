#!/bin/bash
echo Starting BEVM
VBoxManage startvm BEVM --type headless
sleep 10
ssh -p 2223 music@localhost sudo systemctl start apache2
echo BEVM ready
