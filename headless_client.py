import sys
import time
import requests
import concurrent.futures
import argparse

CHUNK_SIZE = 1024 * 1024  # 1MB
SERVER_PORT = 8643

def rank_peers(peers, filename):
    """
    Pings all peers in parallel and returns a sorted list (Fastest -> Slowest).
    Filters out dead nodes.
    """
    print(f"   [Smart Client] Benchmarking latency for {len(peers)} peers...")
    
    def get_latency(peer):
        if ":" in peer:
            ip, port = peer.split(':')
        else:
            ip, port = peer, SERVER_PORT
            
        url = f"http://{ip}:{port}/download/{filename}"
        
        try:
            start = time.time()
            requests.head(url, timeout=2)
            latency = time.time() - start
            return (latency, peer)
        except:
            return (999, peer) # 999 = Dead/Slow

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(get_latency, peers))
    results.sort(key=lambda x: x[0])
    sorted_peers = [r[1] for r in results if r[0] < 999]
    return sorted_peers

def download_file(filename, peers):
    print(f"--- Starting Download: {filename} from {len(peers)} raw peers ---")
    peers = rank_peers(peers, filename)
    
    if not peers:
        print("Error: All peers timed out or are unreachable.")
        return False
        
    # If we have a decent swarm size, drop the slowest half to prevent stragglers.
    if len(peers) > 5:
        original_count = len(peers)
        cutoff = max(10, int(original_count * 0.5)) #changed cut off value here to impact test
        peers = peers[:cutoff]
        print(f"   [Smart Client] Optimization: Dropped {original_count - cutoff} slow peers. Keeping Top {len(peers)}.")
        print(f"   [Smart Client] Active Swarm: {peers}")
    file_size = 0
    valid_metadata_peer = False
    
    # Since 'peers' is now sorted, peers[0] is our best bet for metadata
    try:
        best_peer = peers[0]
        if ":" in best_peer:
            ip, port = best_peer.split(':')
        else:
            ip, port = best_peer, SERVER_PORT
            
        head_url = f"http://{ip}:{port}/download/{filename}"
        response = requests.head(head_url, timeout=3)
    
        if response.status_code == 200:
            file_size = int(response.headers.get('Content-Length', 0))
            print(f"Metadata acquired from {ip} (Fastest Peer). Size: {file_size} bytes")
            valid_metadata_peer = True
    except Exception as e:
        print(f"Warning: Fastest peer failed metadata check. Scan required. {e}")
        # Fallback loop if best peer fails
        for peer in peers:
            try:
                if ":" in peer: ip, port = peer.split(':')
                else: ip, port = peer, SERVER_PORT
                head_url = f"http://{ip}:{port}/download/{filename}"
                response = requests.head(head_url, timeout=2)
                if response.status_code == 200:
                    file_size = int(response.headers.get('Content-Length', 0))
                    valid_metadata_peer = True
                    break
            except: continue

    if not valid_metadata_peer or file_size == 0:
        print("Error: Could not retrieve file size from ANY provided peers.")
        return False

    num_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    try:
        with open(filename, "wb") as f:
            f.seek(file_size - 1)
            f.write(b"\0")
    except Exception as e:
        print(f"Error creating file: {e}")
        return False

    # Dynamic Thread Count (Max 10 or num_peers)
    num_threads = min(len(peers), 10)
    
    def download_chunk(i):
        start_byte = i * CHUNK_SIZE
        end_byte = min((i + 1) * CHUNK_SIZE - 1, file_size - 1)
        peer_index = i
        current_peer = peers[peer_index]
        
        if ":" in current_peer:
            ip, port = current_peer.split(':')
        else:
            ip, port = current_peer, SERVER_PORT

        download_url = f"http://{ip}:{port}/download/{filename}"
        headers = {"Range": f"bytes={start_byte}-{end_byte}"}

        try:
            r = requests.get(download_url, headers=headers, timeout=5)
            if r.status_code == 206 or r.status_code == 200:
                with open(filename, "r+b") as f:
                    f.seek(start_byte)
                    f.write(r.content)
                return True
            else:
                return False
        except Exception:
            return False

    start_time = time.time()
    
    # Run threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_chunk, i) for i in range(num_chunks)]
        concurrent.futures.wait(futures)
    
    total_time = time.time() - start_time
    print(f"Download finished in {total_time:.4f} seconds")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", required=True, help="Comma separated list of IPs")
    parser.add_argument("--file", required=True, help="Filename to download")
    args = parser.parse_args()

    peer_list = [p.strip() for p in args.peers.split(",") if p.strip()]
    
    success = download_file(args.file, peer_list)
    sys.exit(0 if success else 1)