from typing import List
from src.box import Box
from src.sigma_runes.proof_pb2 import Box as PbBox, Boxgroup

def script_to_hex(script: str) -> str:
    box = PbBox()
    box.sigma_script = script.encode('utf-8')
    b = box.SerializeToString().hex()
    return b[2:]  # TODO check if the box part is only 2 bytes.

def boxes_to_hex(boxes: List[Box]) -> str:
    boxgroup = Boxgroup()

    for box in boxes:
        pb_box = boxgroup.boxes.add()
        pb_box.output = 0
        pb_box.sigma_script = box['sigma_script'].encode('utf-8')
        for token in box['tokens']:
            pb_token = pb_box.tokens.add()
            pb_token.id = token['id']
            pb_token.amount = token['amount']
        
        if box.get('r4'):
            pb_box.r4 = box['r4'].encode('utf-8')
            if box.get('r5'):
                pb_box.r5 = box['r5'].encode('utf-8')
                if box.get('r6'):
                    pb_box.r6 = box['r6'].encode('utf-8')
                    if box.get('r7'):
                        pb_box.r7 = box['r7'].encode('utf-8')
                        if box.get('r8'):
                            pb_box.r8 = box['r8'].encode('utf-8')
                            if box.get('r9'):
                                pb_box.r9 = box['r9'].encode('utf-8')

        return boxgroup.SerializeToString().hex()
