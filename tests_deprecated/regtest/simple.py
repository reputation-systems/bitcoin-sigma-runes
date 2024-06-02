import subprocess
import os
import time
import threading
import shutil
import psutil


SILENT = True

def run_command_silently(command):
    # Run the command silently (suppress stdout and stderr)
    if SILENT:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(command.split(), stdout=devnull, stderr=devnull)
    else:
        subprocess.run(command.split())

def run_command_output(command):
    # Run the command and return the output
    if SILENT:
        with open(os.devnull, 'w') as devnull:
            return subprocess.check_output(command.split(), stderr=devnull).decode().strip()
    else:
        return subprocess.check_output(command.split()).decode().strip()

def remove_bitcoin_directory():
    # Define the Bitcoin directory path
    bitcoin_dir = os.path.expanduser("~/.bitcoin")
    # Check if the directory exists
    if os.path.exists(bitcoin_dir):
        print(f"Removing Bitcoin directory: {bitcoin_dir}")
        # Remove the Bitcoin directory
        shutil.rmtree(bitcoin_dir)

def start_bitcoind():
    # Start bitcoind process silently
    bitcoind_command = "bitcoind -regtest -fallbackfee=0.0001"
    print(f"Starting bitcoind with command: {bitcoind_command}")
    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(bitcoind_command.split(), stdout=devnull, stderr=devnull)

def stop_bitcoind():
    print("Stopping bitcoind...")
    run_command_silently("bitcoin-cli -regtest stop")

def create_wallet(wallet_name):
    print(f"Creating wallet: {wallet_name}")
    run_command_silently(f"bitcoin-cli -regtest createwallet {wallet_name}")

def generate_blocks(wallet_name, num_blocks):
    # Get a new address for the specified wallet
    address = run_command_output(f"bitcoin-cli -regtest -rpcwallet={wallet_name} getnewaddress")
    print(f"Generating {num_blocks} blocks to address {address} in wallet {wallet_name}")
    run_command_silently(f"bitcoin-cli -regtest -rpcwallet={wallet_name} generatetoaddress {num_blocks} {address}")

def send_bitcoins(from_wallet, to_wallet, amount):
    print(f"Sending {amount} BTC from wallet {from_wallet} to wallet {to_wallet}")
    # Get a new address from the destination wallet
    to_address = run_command_output(f"bitcoin-cli -regtest -rpcwallet={to_wallet} getnewaddress")
    run_command_silently(f"bitcoin-cli -regtest -rpcwallet={from_wallet} sendtoaddress {to_address} {amount}")

def check_balance(wallet_name):
    # Get the balance of the specified wallet
    balance = run_command_output(f"bitcoin-cli -regtest -rpcwallet={wallet_name} getbalance")
    print(f"Balance of wallet {wallet_name}: {balance} BTC")

def kill_process_using_port(port):
    current_pid = os.getpid()
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            if not conn.pid or conn.pid == current_pid:
                continue  # Ignore the current process
            print(f"Process {conn.pid} is using port {port}. Terminating process...")
            # Terminate the process using the port
            psutil.Process(conn.pid).terminate()
            print("Process terminated successfully.")
            return
    print(f"No process found using port {port}.")

# Define wallet names
wallet_primero = "primero"
wallet_segundo = "segundo"

# Remove the Bitcoin directory if it exists
remove_bitcoin_directory()

# Try to kill any process using port 18443 (if exists)
kill_process_using_port(18443)

print("\n")

# Start bitcoind in a separate thread
bitcoind_thread = threading.Thread(target=start_bitcoind)
bitcoind_thread.start()

# Wait a few seconds to ensure bitcoind has started correctly
time.sleep(5)

# Create wallets
create_wallet(wallet_primero)
create_wallet(wallet_segundo)

# Check the balances of each wallet
check_balance(wallet_primero)
check_balance(wallet_segundo)
print("\n")

# Generate blocks in the first wallet
generate_blocks(wallet_primero, 101)

# Check the balances of each wallet
check_balance(wallet_primero)
check_balance(wallet_segundo)
print("\n")

# Send bitcoins from the first wallet to the second
send_bitcoins(wallet_primero, wallet_segundo, 3.4)

# Check the balances of each wallet
check_balance(wallet_primero)
check_balance(wallet_segundo)
print("\n")

# Generate more blocks in the first wallet
generate_blocks(wallet_primero, 10)

# Check the balances of each wallet
check_balance(wallet_primero)
check_balance(wallet_segundo)
print("\n")

exit()

# Stop bitcoind
stop_bitcoind()

# Wait for the bitcoind thread to finish
bitcoind_thread.join()
