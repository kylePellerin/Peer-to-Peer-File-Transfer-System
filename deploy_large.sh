#!/bin/bash
USER="kpellerin"
FILENAME="big_data.bin"
SIZE="2G" 
SOURCE_LIST="verified_ips.txt"
ACTIVE_LIST="large_swarm_ips.txt"

echo "--- PREPARING LARGE FILE SWARM ---"

#We save this to 'large_swarm_ips.txt' so the test script knows who to call.
shuf -n 20 $SOURCE_LIST > $ACTIVE_LIST

echo "Selected 20 servers. Saved list to $ACTIVE_LIST."

# 2. Deploy ONLY to those 20 servers
while read IP; do
    echo "Configuring $IP..."

    ssh -n -o StrictHostKeyChecking=no $USER@$IP "pkill -u $USER -f peer.py" 2>/dev/null
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "rm -f matrix_movie.mp4 big_data.bin"
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "fallocate -l $SIZE $FILENAME || dd if=/dev/urandom of=$FILENAME bs=1M count=2048 status=none"
    ssh -n -o StrictHostKeyChecking=no $USER@$IP "printf '$FILENAME\n' | nohup python3 peer.py > peer.log 2>&1 &"

done < $ACTIVE_LIST

echo "-----------------------------------"
echo "Deployment Complete. ONLY use '$ACTIVE_LIST' for testing."