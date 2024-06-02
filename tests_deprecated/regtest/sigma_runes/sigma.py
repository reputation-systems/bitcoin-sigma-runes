from sigma_runes.proof_pb2 import Box as PbBox, Boxgroup, Token

def pointers_to_hex(pointers):
    """
    Convert a list of pointers to hexadecimal using Protobuf in Sigma Runes format.
    
    Args:
        pointers (list): List of tuples representing pointers.
            Each tuple should contain (OUTPUT, SIGMA_SCRIPT, TOKENS, R4, R5, R6, R7, R8, R9).
    
    Returns:
        str: Hexadecimal representation of the pointers.
    """
    boxgroup = Boxgroup()
    
    for pointer in pointers:
        box = boxgroup.boxes.add()
        box.output = pointer[0]
        box.sigma_script = pointer[1]
        
        # Adding tokens
        for token_data in pointer[2]:
            token = box.tokens.add()
            token.id = token_data[0]
            token.amount = token_data[1]
        
        # Adding additional data fields r4 to r9
        if len(pointer) > 3:
            box.r4 = pointer[3]
        if len(pointer) > 4:
            box.r5 = pointer[4]
        if len(pointer) > 5:
            box.r6 = pointer[5]
        if len(pointer) > 6:
            box.r7 = pointer[6]
        if len(pointer) > 7:
            box.r8 = pointer[7]
        if len(pointer) > 8:
            box.r9 = pointer[8]
    
    return boxgroup.SerializeToString().hex()

def hex_to_pointers(hex_data):
    """
    Convert hexadecimal data to a list of pointers using Protobuf in Sigma Runes format.
    
    Args:
        hex_data (str): Hexadecimal representation of the pointers.
    
    Returns:
        list: List of tuples representing pointers.
            Each tuple contains (OUTPUT, SIGMA_SCRIPT, TOKENS, R4, R5, R6, R7, R8, R9).
    """
    boxgroup = Boxgroup()
    boxgroup.ParseFromString(bytes.fromhex(hex_data))
    
    pointers = []
    for box in boxgroup.boxes:
        tokens = [(token.id, token.amount) for token in box.tokens]
        pointers.append(
            (box.output, box.sigma_script, tokens, box.r4, box.r5, box.r6, box.r7, box.r8, box.r9)
        )
    
    return pointers

if __name__ == "__main__":
    # Ejemplo de lista de punteros
    pointers_with_extra_fields = [
        (1, b'sigma_script_data', [("token_id_1", 10), ("token_id_2", 20)], b'r4_data', b'r5_data', b'r6_data', b'r7_data', b'r8_data', b'r9_data'),
        (2, b'another_sigma_script', [("token_id_3", 15)], b'r4_data', b'r5_data', b'r6_data', b'r7_data', b'r8_data', b'r9_data'),
        (1, b'third_sigma_script', [], b'r4_data', b'r5_data', b'r6_data', b'r7_data', b'r8_data', b'r9_data')
    ]

    # Convertir a hexadecimal
    hex_data = pointers_to_hex(pointers_with_extra_fields)
    print("Hexadecimal:", hex_data)

    # Convertir de hexadecimal a lista de punteros
    reversed_pointers = hex_to_pointers(hex_data)
    print("Reversed Pointers:", reversed_pointers)
