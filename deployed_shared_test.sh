#!/bin/bash

# The 5 Global Nodes
NODES=("107.23.190.249" "3.144.239.184" "54.151.0.141" "35.159.30.5" "35.72.34.224")
USER="kpellerin"
FILENAME="matrix_movie.mp4"

echo "--- DEPLOYING SHARED FILE SWARM ---"

count=1
for IP in "${NODES[@]}"; do
    echo "[$count/5] Configuring $IP..."
    ssh -o StrictHostKeyChecking=no $USER@$IP "pkill -f peer.py" 2>/dev/null
    ssh -o StrictHostKeyChecking=no $USER@$IP "dd if=/dev/urandom of=$FILENAME bs=1M count=10 status=none"
    scp -o StrictHostKeyChecking=no peer.py $USER@$IP:~/
    # We add '--user' to avoid permission issues
    echo "   Installing libraries on $IP..."
    ssh -o StrictHostKeyChecking=no $USER@$IP "python3 -m pip install --user flask requests urllib3==1.26.15"
    ssh -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py > peer.log 2>&1 &"
    
    ((count++))
done

echo "-----------------------------------"
echo "Swarm deployed. Check server logs for registration."