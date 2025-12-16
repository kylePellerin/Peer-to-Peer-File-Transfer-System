#!/bin/bash

# --- CONFIGURATION ---
USER="kpellerin"                # The user that works!
FILENAME="matrix_movie.mp4"     # The file we are testing with
# ---------------------

echo "--- DEPLOYING SWARM TO ALL IPS ---"

# usage of '3<' prevents SSH from breaking the while loop
while IFS= read -r -u3 IP; do
    # Skip empty lines
    [ -z "$IP" ] && continue

    echo "Configuring $IP..."

    # 1. Kill any old peer process
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "pkill -f peer.py" 2>/dev/null

    # 2. Generate the 100MB file on the server
    #    (Uses fallocate for speed, dd as backup)
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "fallocate -l 100M $FILENAME || dd if=/dev/urandom of=$FILENAME bs=1M count=100 status=none"

    # 3. Upload the peer code
    scp -o StrictHostKeyChecking=no peer.py $USER@$IP:~/

    # 4. Install Flask (Using --user to avoid permission errors)
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "python3 -m pip install --user flask requests"

    # 5. Start the Peer in the background
    #    We feed the filename into it automatically using printf
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py > peer.log 2>&1 &"

    echo "   Success!"

done 3< ips.txt

echo "-----------------------------------"
echo "Deployment Complete. All peers are live."