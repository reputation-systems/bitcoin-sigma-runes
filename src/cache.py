from typing import List, Optional

from src.box import Box
import uuid

class Cache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            cls._instance.boxes = {}  # Main storage for boxes
            cls._instance.wallets_index = {}  # Index for wallets
            cls._instance.scripts_index = {}  # Index for sigma scripts
            cls._instance.tokens_index = {}  # Index for token ids
            cls._instance.transsactions_index = {} # Index for transactions
        return cls._instance

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def add_box(self, wallet: str, box: Box):
        box_id = self._generate_id()
        self.boxes[box_id] = box

        if wallet not in self.wallets_index:
            self.wallets_index[wallet] = []
        self.wallets_index[wallet].append(box_id)

        sigma_script = box['sigma_script']
        if sigma_script not in self.scripts_index:
            self.scripts_index[sigma_script] = []
        self.scripts_index[sigma_script].append(box_id)

        for token in box['tokens']:
            token_id = token['id']
            if token_id not in self.tokens_index:
                self.tokens_index[token_id] = []
            self.tokens_index[token_id].append(box_id)

    def get_all_boxes(self) -> Optional[List[Box]]:
        return self.boxes.values()

    def get_boxes_by_wallet(self, wallet: str) -> Optional[List[Box]]:
        box_ids = self.wallets_index.get(wallet, [])
        return [self.boxes[box_id] for box_id in box_ids]

    def get_boxes_by_script(self, sigma_script: str) -> Optional[List[Box]]:
        box_ids = self.scripts_index.get(sigma_script, [])
        return [self.boxes[box_id] for box_id in box_ids]

    def get_boxes_by_token(self, token_id: str) -> Optional[List[Box]]:
        box_ids = self.tokens_index.get(token_id, [])
        return [self.boxes[box_id] for box_id in box_ids]
