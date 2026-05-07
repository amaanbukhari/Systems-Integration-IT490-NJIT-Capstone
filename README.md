Each team member hosts ONE VM.

VM names:

RMQVM  
DBVM  
BEVM  
FEVM  

Username inside every VM:

music  

Each person only sets up and runs their own VM.


On your computer:

1. Install VirtualBox
2. Create a new Ubuntu Server VM
3. During setup:
   - Username: music
   - Give sudo access


After logging into the VM:

sudo apt update -y
sudo apt upgrade -y
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

Make sure SSH is running:
sudo systemctl status ssh

Only install what your VM needs.


### RMQVM (RabbitMQ)

sudo apt install -y rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server

### DBVM (MySQL)

sudo apt install -y mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql

### BEVM (Backend – Apache + PHP)

sudo apt install -y apache2 php libapache2-mod-php
sudo systemctl enable apache2
sudo systemctl start apache2

sudo mkdir -p /var/www/thisIsMusic
sudo chown -R music:music /var/www/thisIsMusic

Put backend files in:
```
/var/www/thisIsMusic

### FEVM (Frontend – Apache + PHP)

sudo apt install -y apache2 php libapache2-mod-php
sudo systemctl enable apache2
sudo systemctl start apache2

sudo mkdir -p /var/www/thisIsMusic
sudo chown -R music:music /var/www/thisIsMusic

Put frontend files in:

- /var/www/thisIsMusic

RMQVM:
sudo systemctl start rabbitmq-server

DBVM:
sudo systemctl start mysql
BEVM / FEVM:

sudo systemctl start apache2


Final Check

- VM name correct
- Username is music
- SSH works
- Service starts without errors

