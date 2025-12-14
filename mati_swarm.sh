#!/bin/bash

# A diverse list of 5 Public IPs (Excluding the servers)
NODES=(
    "107.23.190.249"  # Virginia (Peer 1)
    "3.144.239.184"   # Ohio     (Peer 2)
    "54.151.0.141"    # Cali     (Peer 3)
    "35.159.30.5"     # Frankfurt(Peer 4)
    "35.72.34.224"    # Tokyo    (Peer 5)
)

USER="mgibbons"

echo "--- DEPLOYING GLOBAL SWARM ---"

count=1
for IP in "${NODES[@]}"; do
    echo "[$count/5] Deploying to $IP..."
    
    ssh -o StrictHostKeyChecking=no $USER@$IP "pkill -f peer.py" 2>/dev/null

    FILENAME="data${count}.txt"
    ssh -o StrictHostKeyChecking=no $USER@$IP "echo 'Hello from $IP' > $FILENAME"
    scp -o StrictHostKeyChecking=no peer.py $USER@$IP:~/
    ssh -o StrictHostKeyChecking=no $USER@$IP "pip3 install flask requests urllib3==1.26.15 > /dev/null 2>&1"
    ssh -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py > peer.log 2>&1 &"

    echo "   -> Peer $count is LIVE sharing '$FILENAME'"
    ((count++))
done

echo "-----------------------------------"
echo "Swarm is Active. You can now run 'python3 peer.py' locally and SEARCH for:"
echo "data_from_peer1.txt ... data_from_peer5.txt"