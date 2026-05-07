#!/usr/bin/env bash
set -euo pipefail

DB_NAME="this_is_music"
SQL_FILE="$HOME/IT490/database/init_db.sql"

echo "===================================="
echo " Starting MySQL Database Service"
echo "===================================="

sudo -n systemctl enable --now mysql

echo
echo "MySQL status (first 10 lines):"
sudo systemctl status mysql --no-pager | head -n 10

echo
echo "===================================="
echo " Database Setup"
echo "===================================="
echo "Database name: $DB_NAME"
echo "Schema file: $SQL_FILE"
echo

read -p "Do you want to initialize/update the database schema? (y/n): " answer

if [[ "$answer" == "y" || "$answer" == "Y" ]]; then

    echo
    echo "Creating database and loading schema..."

    sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
USE $DB_NAME;
SOURCE $SQL_FILE;
EOF

    echo
    echo "Schema loaded successfully."

else
    echo
    echo "Skipping schema initialization."
fi

echo
echo "===================================="
echo "Database setup completed."
echo "===================================="
