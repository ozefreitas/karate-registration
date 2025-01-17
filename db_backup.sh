#!/bin/bash

# Backup SQLite database
cp /home/karatescorappregistration/karate-registration/db.sqlite3 /home/karatescorappregistration/karate-registration/db_backup.sqlite3

# Optional: Print a success message
echo "Database backup completed successfully!"