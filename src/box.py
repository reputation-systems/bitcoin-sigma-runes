from typing import Optional, List
from typing_extensions import TypedDict

class Token(TypedDict):
    id: str
    amount: int

class Box(TypedDict):
    sigma_script: str           # Script to be validated to spend the funds.
    tokens: List[Token]           # Tokens held within the box.
    r4: Optional[str]           # Additional data field 4.
    r5: Optional[str]           # Additional data field 5.
    r6: Optional[str]           # Additional data field 6.
    r7: Optional[str]           # Additional data field 7.
    r8: Optional[str]           # Additional data field 8.
    r9: Optional[str]           # Additional data field 9.