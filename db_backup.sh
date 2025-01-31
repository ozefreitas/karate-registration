#!/bin/bash

# Define the backup file pattern
BACKUP_PATTERN="/home/karatescorappregistration/karate-registration/db_backup_*.sqlite3"

# Remove any existing backup files
rm -f $BACKUP_PATTERN

# Get the current date in YYYY-MM-DD format
DATE=$(date +"%Y-%m-%d")

# Define the source and destination paths
SOURCE="/home/karatescorappregistration/karate-registration/db.sqlite3"
DESTINATION="/home/karatescorappregistration/karate-registration/db_backup_$DATE.sqlite3"

# Copy the database file
cp $SOURCE $DESTINATION

# Optional: Print a success message
echo "Database backup completed successfully!"