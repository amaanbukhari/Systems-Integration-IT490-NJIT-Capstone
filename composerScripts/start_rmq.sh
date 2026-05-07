#!/bin/bash
echo Starting RMQVM
VBoxManage startvm RMQVM --type headless
sleep 10
ssh -p 2221 music@localhost sudo systemctl start rabbitmq-server
echo RMQVM ready
