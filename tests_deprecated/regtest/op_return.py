import subprocess
import os
import time
import threading
import shutil
from typing import List
import psutil
import json


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

def create_op_return_transaction(wallet_name, data) -> str:
    try:
        # List unspent transactions to get a UTXO
        unspent_txs = run_command_output(f"bitcoin-cli -regtest -rpcwallet={wallet_name} listunspent")
        unspent_txs = json.loads(unspent_txs)

        if not unspent_txs:
            print("No unspent transactions available.")
            return None

        # Select the first UTXO as the input for the new transaction
        utxo = unspent_txs[0]
        txid = utxo['txid']
        vout = utxo['vout']

        # Create JSON for the transaction input
        input_json = json.dumps([{"txid": txid, "vout": vout}])

        fee_amount = 0.00001

        # Create JSON for the transaction output (OP_RETURN)
        output_json = json.dumps([{"data": data}, {utxo["address"]: utxo["amount"]-fee_amount}])

        try:
            # Create a transaction with an OP_RETURN output and capture the raw transaction hex
            raw_tx = subprocess.check_output(
                f"bitcoin-cli -regtest -rpcwallet={wallet_name} createrawtransaction '{input_json}' '{output_json}'",
                shell=True,  # This allows using the shell to execute the command
                encoding='utf-8',  # Decode the output as UTF-8
            ).strip()
        except subprocess.CalledProcessError as e:
            # Handle error
            print("Error creating raw transaction:", e)

        # Sign the transaction
        try:
            signed_tx = subprocess.run(
                f"bitcoin-cli -regtest -rpcwallet={wallet_name} signrawtransactionwithwallet '{raw_tx}'",
                shell=True,
                check=True,
                capture_output=True,
                encoding='utf-8'
            )
            signed_hex = json.loads(signed_tx.stdout.strip())['hex']
            
            # Send the transaction
            sent_txid = subprocess.run(
                f"bitcoin-cli -regtest -rpcwallet={wallet_name} sendrawtransaction '{signed_hex}'",
                shell=True,
                check=True,
                capture_output=True,
                encoding='utf-8'
            )
            sent_txid = sent_txid.stdout.strip()
            print(f"Transaction sent. TXID: {sent_txid}")
        except subprocess.CalledProcessError as e:
            print("Error:", e)

        return sent_txid

    except subprocess.CalledProcessError as e:
        print(f"Error creating OP_RETURN transaction: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None
    
def fetch_rune_txs(wallet_name: str, data: str) -> List[str]:
    print("Fetching transactions with OP_RETURN data...")
    try:
        # List transactions for the wallet
        tx_list_output = run_command_output(f"bitcoin-cli -regtest -rpcwallet={wallet_name} listtransactions '*' 100")
        tx_list_output = subprocess.check_output(
                f"bitcoin-cli -regtest -rpcwallet={wallet_name} listtransactions '*' 100",
                shell=True,
                encoding='utf-8'
            )
        tx_list = json.loads(tx_list_output)

        rune_txs = []
        # Iterate through transactions
        for tx in tx_list:
            # Check if transaction has OP_RETURN output
            if 'vout' in tx:
                # Get detailed transaction information
                tx_details_output = run_command_output(f"bitcoin-cli -regtest -rpcwallet={wallet_name} gettransaction {tx['txid']}")
                tx_details = json.loads(tx_details_output)
                if data in tx_details['hex']:
                    rune_txs.append(tx_details['txid'])
        
        return rune_txs

    except subprocess.CalledProcessError as e:
        print(f"Error fetching transactions: {e}")
        return []

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

print("Creating transaction with OP_RETURN")
op_return_data = "5201010000010002010014000000"  # Rune.
data_txid = create_op_return_transaction(wallet_primero, op_return_data)
print(f"Transaction with OP_RETURN created. TXID: {data_txid}")

# Generate more blocks in the first wallet
generate_blocks(wallet_segundo, 10)

# Check the balances of each wallet
check_balance(wallet_primero)
check_balance(wallet_segundo)
print("\n")

# Get the txs with runes.
data_txs = fetch_rune_txs(wallet_primero, op_return_data)

assert data_txid in data_txs

# Stop bitcoind
stop_bitcoind()

# Wait for the bitcoind thread to finish
bitcoind_thread.join()
