FILE="matrix_movie.mp4"
LIST="large_swarm_ips.txt"

echo "Starting Large File Scalability Test..."

for i in {1..20}; do
    echo "TESTING PEER COUNT: $i"
    # Shuffle from the SPECIFIC list of 20
    PEERS=$(shuf -n $i $LIST | tr '\n' ',' | sed 's/,$//')
    python3 headless_client.py --peers "$PEERS" --file "$FILE"
    sleep 5
done