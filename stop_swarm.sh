#!/bin/bash
USER="kpellerin"
IPS="verified_ips.txt"

echo "--- SHUTTING DOWN SWARM ---"

while read IP; do
    echo "Stopping $IP..."
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "pkill -u $USER -f peer.py" 2>/dev/null
done < $IPS

echo "-----------------------------------"
echo "Swarm deactivated."