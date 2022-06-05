import base58
from solana.keypair import Keypair

# ADD VALUES HERE
LOCKED_AIRDROP_SECRET_KEY = ""
_SENDER_WALLET_ADDRESS_PRIVATE_KEY = ""
TOKEN_MINT_ADDRESS = ""
TOKEN_DECIMAL = 1000000000  # replace it with the Decimals of your token

INIT_STREAM_INSTRUCTION = 3
WITHDRAW_TOKEN_STRING = "withdraw_token"
RPC_CLUSTER_URL = "https://api.mainnet-beta.solana.com"     # make sure you use third-party RPC Endpoint (like Syndica) since this endpoint is not stable.
ZEBEC_PROGRAM_ID = "AknC341xog56SrnoK6j3mUvaD1Y7tYayx1sxUGpeYWdX"

SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

API_ZEBEC_URL = "https://api.zebec.io"
FROM_WALLET_KEYPAIR = Keypair.from_secret_key(
    base58.b58decode(_SENDER_WALLET_ADDRESS_PRIVATE_KEY)
)