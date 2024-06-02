import subprocess
import os
import shutil
from typing import List
import psutil
import json

from enum import Enum

class BitcoinNetwork(Enum):
    MAINNET = ""
    TESTNET = "-testnet"
    REGTEST = "-regtest"


class BitcoinInterface:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BitcoinInterface, cls).__new__(cls)
        return cls._instance

    def __init__(self, silent=True, network=BitcoinNetwork.REGTEST):
        if not hasattr(self, "_initialized"):
            self.silent = silent
            self.network = network.value
            self.bitcoin_dir = os.path.expanduser("~/.bitcoin")
            self.devnull = open(os.devnull, 'w')
            self._initialized = True

    def __del__(self):
        self.devnull.close()

    def _run_command_silently(self, command):
        if self.silent:
            subprocess.run(command.split(), stdout=self.devnull, stderr=self.devnull)
        else:
            subprocess.run(command.split())

    def _run_command_output(self, command):
        if self.silent:
            return subprocess.check_output(command.split(), stderr=self.devnull).decode().strip()
        else:
            return subprocess.check_output(command.split()).decode().strip()

    def remove_bitcoin_directory(self):
        if os.path.exists(self.bitcoin_dir):
            print(f"Removing Bitcoin directory: {self.bitcoin_dir}")
            shutil.rmtree(self.bitcoin_dir)

    def start_bitcoind(self):
        bitcoind_command = f"bitcoind {self.network} -fallbackfee=0.0001"
        print(f"Starting bitcoind with command: {bitcoind_command}")
        subprocess.Popen(bitcoind_command.split(), stdout=self.devnull, stderr=self.devnull)

    def stop_bitcoind(self):
        print("Stopping bitcoind...")
        self._run_command_silently(f"bitcoin-cli {self.network} stop")

    def create_wallet(self, wallet_name):
        print(f"Creating wallet: {wallet_name}")
        self._run_command_silently(f"bitcoin-cli {self.network} createwallet {wallet_name}")

    def list_wallets(self):
        print(f"List wallets")
        self._run_command_silently(f"bitcoin-cli {self.network} listwallets")

    def generate_blocks(self, wallet_name, num_blocks=101):
        address = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} getnewaddress")
        print(f"Generating {num_blocks} blocks to address {address} in wallet {wallet_name}")
        self._run_command_silently(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} generatetoaddress {num_blocks} {address}")

    def send_bitcoins(self, from_wallet, to_wallet, amount):
        print(f"Sending {amount} BTC from wallet {from_wallet} to wallet {to_wallet}")
        to_address = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={to_wallet} getnewaddress")
        self._run_command_silently(f"bitcoin-cli {self.network} -rpcwallet={from_wallet} sendtoaddress {to_address} {amount}")

    def check_balance(self, wallet_name):
        balance = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} getbalance")
        print(f"Balance of wallet {wallet_name}: {balance} BTC")

    def create_op_return_transaction(self, wallet_name: str, data: str) -> str:
        data = data[:160] # TODO https://stackoverflow.com/questions/24845429/maximum-size-of-data-bitcoin-op-return-tx-can-handle#:~:text=Using%20the%20OP_RETURN%20script%20you,will%20let%20larger%20data%20through.&text=According%20above%20link%20https%3A%2F%2F,put%20up%20to%2083%20bytes.
        try:
            unspent_txs = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} listunspent")
            unspent_txs = json.loads(unspent_txs)

            if not unspent_txs:
                print("No unspent transactions available.")
                return None

            utxo = unspent_txs[0]
            txid = utxo['txid']
            vout = utxo['vout']

            input_json = json.dumps([{"txid": txid, "vout": vout}])
            fee_amount = 0.00001
            output_json = json.dumps([{"data": data}, {utxo["address"]: utxo["amount"]-fee_amount}])

            print(f"output json ->  {output_json}")

            raw_tx = subprocess.check_output(
                f"bitcoin-cli {self.network} -rpcwallet={wallet_name} createrawtransaction '{input_json}' '{output_json}'",
                shell=True,
                encoding='utf-8',
            ).strip()

            signed_tx = subprocess.run(
                f"bitcoin-cli {self.network} -rpcwallet={wallet_name} signrawtransactionwithwallet '{raw_tx}'",
                shell=True,
                check=True,
                capture_output=True,
                encoding='utf-8'
            )
            signed_hex = json.loads(signed_tx.stdout.strip())['hex']

            sent_txid = subprocess.run(
                f"bitcoin-cli {self.network} -rpcwallet={wallet_name} sendrawtransaction '{signed_hex}'",
                shell=True,
                check=True,
                capture_output=True,
                encoding='utf-8'
            )
            sent_txid = sent_txid.stdout.strip()
            print(f"Transaction sent. TXID: {sent_txid}")

            tx_details_output = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} gettransaction {sent_txid}")
            tx_details = json.loads(tx_details_output)

            print(f"\ntx details -> {tx_details}\n")

            return sent_txid

        except subprocess.CalledProcessError as e:
            print(f"Error creating OP_RETURN transaction: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None

    def fetch_rune_txs(self, wallet_name: str, data: str) -> List[str]:
        data = data[:160]  # TODO https://stackoverflow.com/questions/24845429/maximum-size-of-data-bitcoin-op-return-tx-can-handle#:~:text=Using%20the%20OP_RETURN%20script%20you,will%20let%20larger%20data%20through.&text=According%20above%20link%20https%3A%2F%2F,put%20up%20to%2083%20bytes.
        print(f"data -> {data}")
        try:
            tx_list_output = subprocess.check_output(
                f"bitcoin-cli {self.network} -rpcwallet={wallet_name} listtransactions '*' 100",
                shell=True,
                encoding='utf-8'
            ).strip()
            tx_list = json.loads(tx_list_output)

            rune_txs = []
            for tx in tx_list:
                if 'vout' in tx:
                    tx_details_output = self._run_command_output(f"bitcoin-cli {self.network} -rpcwallet={wallet_name} gettransaction {tx['txid']}")
                    tx_details = json.loads(tx_details_output)
                    if data in tx_details['hex']: # TODO Tx don't appear.
                        rune_txs.append(tx_details['txid'])

            return rune_txs

        except subprocess.CalledProcessError as e:
            print(f"Error fetching transactions: {e}")
            return []

    def kill_process_using_port(self, port):
        current_pid = os.getpid()
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                if not conn.pid or conn.pid == current_pid:
                    continue
                print(f"Process {conn.pid} is using port {port}. Terminating process...")
                psutil.Process(conn.pid).terminate()
                print("Process terminated successfully.")
                return
        print(f"No process found using port {port}.")
