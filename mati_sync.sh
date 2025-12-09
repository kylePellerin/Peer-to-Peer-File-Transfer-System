#!/bin/bash

PRIMARY="54.205.35.150"
BACKUP="54.226.158.73"
USER="mgibbons"

echo "--- Syncing to PRIMARY ($PRIMARY) ---"
scp -o StrictHostKeyChecking=no *.java $USER@$PRIMARY:~/
ssh -o StrictHostKeyChecking=no $USER@$PRIMARY "javac -cp '.:lib/*' *.java"
echo "Done."

echo "--- Syncing to BACKUP ($BACKUP) ---"
scp -o StrictHostKeyChecking=no *.java $USER@$BACKUP:~/
ssh -o StrictHostKeyChecking=no $USER@$BACKUP "javac -cp '.:lib/*' *.java"
echo "Done."

echo "--- All servers updated and compiled! ---"