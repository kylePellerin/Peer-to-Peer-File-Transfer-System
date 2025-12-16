#!/bin/bash
# test_resilience.sh

PRIMARY_IP="54.205.35.150"
USER="kpellerin"
FILE="matrix_movie.mp4"
LIST="large_swarm_ips.txt"

echo "--- STARTING RESILIENCE TEST ---"

echo "[Client] Requesting file..."
PEERS=$(shuf -n 10 $LIST | tr '\n' ',' | sed 's/,$//')
python3 headless_client.py --peers "$PEERS" --file "$FILE" > client_output.log 2>&1 &
CLIENT_PID=$!
sleep 3

echo "   "
echo "!!! KILLING PRIMARY SERVER NOW !!!"
# We SSH in and brutally(TM) kill the python process
ssh -o StrictHostKeyChecking=no $USER@$PRIMARY_IP "pkill -f primary_server.py"
echo "!!! PRIMARY SERVER DEAD !!!"

wait $CLIENT_PID

echo "   "
echo "--- TEST COMPLETE ---"
echo "Checking logs for success..."
tail -n 5 client_output.log