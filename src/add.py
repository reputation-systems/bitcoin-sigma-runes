from hashlib import sha256
from uuid import uuid4
from src.box import Box
from src.bitcoin_interface import BitcoinInterface
from src.sigma_runes.sigma import boxes_to_hex, script_to_hex
from src.cache import Cache

TEST = False

def add(box: Box) -> str:
    wallet_name = str(uuid4())
    BitcoinInterface().create_wallet(wallet_name=wallet_name)

    BitcoinInterface().generate_blocks(wallet_name=wallet_name)
    BitcoinInterface().check_balance(wallet_name=wallet_name)

    if not box['tokens'][0]['id']:
        box['tokens'][0]['id'] = sha256(str(box).encode('utf-8')).hexdigest()

    data = boxes_to_hex([box])
    data_tx = BitcoinInterface().create_op_return_transaction(wallet_name=wallet_name, data=data)

    Cache().add_box(box=box, wallet=wallet_name)

    if TEST:
        # This is only for test.
        BitcoinInterface().generate_blocks(wallet_name=wallet_name)
        runes_tx = BitcoinInterface().fetch_rune_txs(wallet_name=wallet_name, data=script_to_hex(script=box['sigma_script']))
        print("runes tx -> ", runes_tx)

    return data_tx