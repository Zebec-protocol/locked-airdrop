from construct import Adapter, Bytes
from solana.publickey import PublicKey
from borsh_construct import U8, U64, CStruct

class _PubKey(Adapter):
    def __init__(self):
        super().__init__(Bytes(32))
    
    def _decode(self, obj, context, path):
        return PublicKey(obj)
    
    def _encode(self, obj, context, path):
        return bytes(obj)

PubKey = _PubKey()

# Init Stream Schema
STREAM_PDA_SCHEMA = CStruct(
    "instruction" / U8,
    "start_time" / U64,
    "end_time" / U64,
    "amount" / U64
)