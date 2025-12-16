#!/bin/bash
USER="kpellerin"
FILENAME="matrix_movie.mp4"
IPS="verified_ips.txt"

echo "--- STARTING SWARM (NO INSTALLS) ---"

while read IP; do
    echo "Booting $IP..."
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "pkill -u $USER -f peer.py" 2>/dev/null
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py > peer.log 2>&1 &"

done < $IPS

echo "-----------------------------------"
echo "All servers restarted."