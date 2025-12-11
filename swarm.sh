#!/bin/bash

# Clean up previous run
rm -rf swarm_peer*
mkdir -p swarm_logs

echo "--- LAUNCHING P2P SWARM ---"

# Launch 5 Peers
for i in {1..5}
do
   # 1. Create a dedicated folder for this peer
   FOLDER="swarm_peer$i"
   mkdir -p $FOLDER
   
   # 2. Copy the code into it
   cp peer.py $FOLDER/
   
   # 3. Create a unique file for them to share
   FILENAME="data_$i.txt"
   echo "This is the content of data_$i" > "$FOLDER/$FILENAME"
   
   # 4. Pick a unique port (8700, 8701, etc)
   PORT=$((8700 + i))
   
   # 5. RUN IT IN THE BACKGROUND
   # We pipe the inputs: "FILENAME" + newline + "3" (Listen Mode)
   # We redirect output to a log file so it doesn't clutter your screen
   cd $FOLDER
   printf "$FILENAME\n3\n" | python3 peer.py $PORT > ../swarm_logs/peer$i.log 2>&1 &
   
   # Save the Process ID so we can kill it later
   PID=$!
   echo "Started Peer $i on Port $PORT sharing '$FILENAME' (PID: $PID)"
   
   cd ..
   sleep 1
done

echo "--------------------------------"
echo "Swarm is live! Check 'swarm_logs/' to see their status."
echo "Run './kill_swarm.sh' to stop them."