import json
import requests

import pandas as pd

from solana.publickey import PublicKey
from solana.keypair import Keypair

from solana.rpc.api import Client
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction, TransactionInstruction, AccountMeta


from constants import API_ZEBEC_URL, FROM_WALLET_KEYPAIR, INIT_STREAM_INSTRUCTION, LOCKED_AIRDROP_SECRET_KEY, RPC_CLUSTER_URL, TOKEN_DECIMAL, TOKEN_MINT_ADDRESS, TOKEN_PROGRAM_ID, WITHDRAW_TOKEN_STRING, ZEBEC_PROGRAM_ID
from utils import STREAM_PDA_SCHEMA


class LockedAirdrop:

    def __init__(self):
        self.client = Client(endpoint=RPC_CLUSTER_URL, commitment=Confirmed)
        self.secret_key = LOCKED_AIRDROP_SECRET_KEY
        self.sender_keypair = FROM_WALLET_KEYPAIR
        self.sender_address = self.sender_keypair.public_key
        self.zebec_program_address = PublicKey(ZEBEC_PROGRAM_ID)
        self.token_program_address = PublicKey(TOKEN_PROGRAM_ID)
        self.access_token = self.get_access_token()
    
    def get_recent_blockhash(self):
        return (
        self.client.get_recent_blockhash()
            ['result']
            ['value']
            ['blockhash']
            .encode('utf-8')
    )

    def init_stream(self):
        receiver_address = PublicKey(self.receiver)
        token_mint_address = PublicKey(self.token_mint_address)

        withdraw_escrow_address, _ = PublicKey.find_program_address(
            [WITHDRAW_TOKEN_STRING.encode("utf-8"), bytes(self.sender_address), bytes(token_mint_address)],
            self.zebec_program_address
        )

        escrow = Keypair()

        encoded_data = STREAM_PDA_SCHEMA.build({
            "instruction": INIT_STREAM_INSTRUCTION,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "amount": self.amount * TOKEN_DECIMAL      
        })

        instruction = TransactionInstruction(
            [
                AccountMeta(self.sender_address, True, True),
                AccountMeta(receiver_address, False, True),
                AccountMeta(escrow.public_key, True, True),
                AccountMeta(withdraw_escrow_address, False, True),
                AccountMeta(self.token_program_address, False, False),
                AccountMeta(SYS_PROGRAM_ID, False, False),
                AccountMeta(token_mint_address, False, False)
            ],
            self.zebec_program_address,
            encoded_data
        )

        transaction = Transaction().add(instruction)

        try:
            transaction.recent_blockhash = self.get_recent_blockhash()
            transaction.fee_payer = self.sender_address

            signature = self.client.send_transaction(transaction, self.sender_keypair, escrow)["result"]
            self.client.confirm_transaction(signature, Confirmed)

            data = {
                "receiver": self.receiver,
                "start": self.start_time,
                "end": self.end_time,
                "token": self.token_mint_address,
                "amount": self.amount,
                "transaction_name": self.transaction_name,
                "status": "scheduled",
                "pda": str(escrow.public_key),
                "withdrawn": 0,
                "transaction_id": signature
            }

            response = self.save_metadata(data)
            if response is None:
                return {
                    "status": "error",
                    "message": "failed to save tx meta data",
                    "data": {
                        "receiver": self.receiver,
                        "transaction_name": self.transaction_name,
                        "amount": self.amount,
                        "pda": None,
                        "transactionHash": None,
                    }
                }
            return {
                "status": "success",
                "message": "transaction initiated",
                "data": {
                    "receiver": self.receiver,
                    "transaction_name": self.transaction_name,
                    "amount": self.amount,
                    "transactionHash": signature,
                    "pda": str(escrow.public_key)
                }
            }

        except:
            return {
                "status": "error",
                "message": "transaction failed to init",
                "data": {
                        "receiver": self.receiver,
                        "transaction_name": self.transaction_name,
                        "amount": self.amount,
                        "transactionHash": None,
                        "pda": None
                    }
            }

    def save_metadata(self, data):
        url = API_ZEBEC_URL + "/outgoing"
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        # return True
        response = None
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
        except Exception as e:
            print(e, "Exception on saving metadata")
        return response

    def get_access_token(self):

        url = API_ZEBEC_URL + '/client-login'
        payload = json.dumps({
            "wallet_address": str(self.sender_address),
            "secret_key": self.secret_key
        })
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        token = response.json()["access_token"]
        return token

    def check_error(self):
        if self.master_file:
            if self.master_file[-4:] != ".csv":
                if self.debug:
                    print("ERROR: master_file must be a CSV Location")
                quit()

            try:
                self.df = pd.read_csv(self.master_file)
            except:
                if self.debug:
                    print("ERROR: master_file could not be found")
                quit()
            
            try:
                self.df[self.transaction_name_key]
            except:
                if self.debug:
                    print("ERROR: transaction_name_key not found in master_file")
                quit()
            
            try:
                self.df[self.receiver_key]
            except:
                if self.debug:
                    print("ERROR: receiver_key not found in master_file")
                quit()

            try:
                self.df[self.start_time_key]
            except:
                if self.debug:
                    print("ERROR: start_time_key not found in master_file")
                quit()
            
            try:
                self.df[self.end_time_key]
            except:
                if self.debug:
                    print("ERROR: end_time_key not found in master_file")
                quit()
            
            try:
                self.df[self.amount_key]
            except:
                if self.debug:
                    print("ERROR: amount_key not found in master_file")
                quit()
            
            if self.output_file:
                if self.output_file[-4:] != ".csv":
                    if self.debug:
                        print("ERROR: output_file must be a csv location")
                    quit()

    def initialize(
        self, master_file=False, output_file=False, receiver_key=False,
        start_time_key=False, end_time_key=False, amount_key=False, transaction_name_key=False,
        token_mint_address=False, run_script=False, log=False, debug=False
    ):
        data = []
        self.master_file = master_file
        self.output_file = output_file
        self.receiver_key = receiver_key
        self.start_time_key = start_time_key
        self.end_time_key = end_time_key
        self.amount_key = amount_key
        self.transaction_name_key = transaction_name_key
        self.token_mint_address = token_mint_address
        self.script = run_script
        self.debug = debug
        self.log = log


        self.check_error()

        if self.script:
            data = self.run_script()
        
        if output_file:
            df = pd.DataFrame(data)
            df.to_csv(self.output_file, columns=df.columns, index=False)
        
        return True

    def run_script(self):
        all_response = []

        if self.master_file:
            for index, row in self.df.iterrows():
                try:
                    self.receiver = row[self.receiver_key]
                    self.start_time = row[self.start_time_key]
                    self.end_time = row[self.end_time_key]
                    self.amount = row[self.amount_key]
                    self.transaction_name = row[self.transaction_name_key]

                    print(f"{index+1}/{self.df.shape[0]}")
                    if self.log:
                        print(f"{self.receiver}")
                    
                    response = self.init_stream()

                    if self.log:
                        for a in response:
                            print(f'\t{a}: {response[a]}')
                        print()
                    all_response.append(response["data"])
                except:
                    print(f"\tFailed")
                    metadata = {
                        "receiver": self.receiver,
                        "transaction_name": self.transaction_name,
                        "amount": self.amount,
                        "transactionHash": None,
                        "pda": None
                    }
                    all_response.append(metadata)
        return all_response
                    


if __name__ == "__main__":

    locked_airdrop = LockedAirdrop()
    locked_airdrop.initialize(
        master_file="wallet.csv",
        output_file= "./wallet_response.csv",
        receiver_key="recipient",
        start_time_key="start_time",
        end_time_key="end_time",
        amount_key="amount",
        transaction_name_key="transaction_name",
        token_mint_address=TOKEN_MINT_ADDRESS,
        run_script=True,
        log=True,
        debug=True    
    )

    print("Completed!!!!")

        


