#!/bin/bash
USER="kpellerin"
FILENAME="matrix_movie.mp4"

# The 5 working servers
# (We use a file here, make sure working_ips.txt exists)
IPS="working_ips.txt"

echo "--- DEPLOYING VIRTUAL SWARM (Ports 8801-8804) ---"

while read IP; do
    echo "Configuring $IP..."
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "pkill -u $USER -f peer.py" 2>/dev/null
    scp -o StrictHostKeyChecking=no peer.py $USER@$IP:~/
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "fallocate -l 100M $FILENAME || dd if=/dev/urandom of=$FILENAME bs=1M count=100 status=none"
    echo "   Launching 4 virtual peers..."
    for PORT in {8801..8804}; do
        # Pass the port number to the script
        ssh -n -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py $PORT > peer_$PORT.log 2>&1 &"
    done

done < clean_ips.txt

echo "Done. 20 Peers are running on ports 8801-8804."