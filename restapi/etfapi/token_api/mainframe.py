import os
import yaml
import json
import base58
import logging
import time

from metaplex.utils.execution_engine import execute
from solana.account import Account
from solana.transaction import Transaction
from cryptography.fernet import Fernet

from .mtransactions import wallet, deploy, topup, mint, send
from copy import copy

def get_config(config_path=os.path.join(os.path.dirname(__file__), "config.yaml")):
    with open(config_path, "rb") as fl:
        config = yaml.safe_load(fl)

    return config

config = get_config()
keypair_path = config["keypair_config"]["keypair_path"]
api_endpoint = config["rpc_config"]["api_endpoint"]
fernet_sym_key = Fernet.generate_key()

logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), config["rpc_config"]["logfile_name"]), level=logging.INFO)


def initialize_core_account(keypair_path, fernet_key):
    with open(keypair_path, "rb") as fl:
        keypair = json.load(fl)

    private_key = keypair[:32]

    account = Account(private_key)
    cipher = Fernet(fernet_key)

    return account, private_key, cipher

def execute_transaction(transaction_wrapper, api_endpoint, max_retries=99, skip_confirmation=False, max_timeout=1, target=20, finalized=True):
    transaction_success = False
    attempts = 0

    while not transaction_success:
        transaction, signers, other_data = transaction_wrapper()

        try:
            resp = execute(
                api_endpoint,
                transaction,
                signers,
                max_retries=1,
                skip_confirmation=skip_confirmation,
                max_timeout=max_timeout,
                target=target,
                finalized=finalized,
            )
            resp["status"] = 200

            for v,k in other_data.items():
                resp["other_data"] = {}
                resp["other_data"][v] = k

            return copy(resp)
        except:
            if attempts < max_retries:
                attempts += 1
                continue
            else:
                logging.error("Transaction failure")
                return json.dumps({"status": 400})

def create_account():
    return json.loads(wallet())

def new_transaction():
    tx = Transaction()
    signers = []

    return tx, signers

core_account, core_priv_key, cipher = initialize_core_account(keypair_path, fernet_sym_key)


def mint_master_edition(api_endpoint, core_account, core_priv_key, cipher, nft_config):
    contract_name = nft_config["contract_name"]
    contract_symbol = nft_config["contract_symbol"]
    mint_authority = nft_config["mint_authority"]
    metadata_url = nft_config["metadata_url"]

    logging.info("Minting master edition {0} (symbol: {0}, authority: {1}, metadata: {2})".format(contract_name, contract_symbol, mint_authority, metadata_url))

    def deploy_token():
        tx, signers = new_transaction()

        mint_dest_account = create_account()

        tx, signers, contract_key = deploy(api_endpoint, core_account, contract_name, contract_symbol, tx=tx, signers=signers)

        return tx, signers, {"contract_key": contract_key}

    t_a = time.time()
    deployed_token = execute_transaction(deploy_token, api_endpoint)
    contract_key = deployed_token["other_data"]["contract_key"]
    t_b = time.time()

    logging.info("Contract {0} deployed at: {1} (time elapsed: {2})".format(contract_name, contract_key, str(round(t_b - t_a, 4))))

    def deploy_mint():
        while True:
            try:
                tx, signers = new_transaction()
                tx, signers = mint(api_endpoint, core_account, contract_key, mint_authority, metadata_url, supply=1, tx=tx, signers=signers)

                return tx, signers, {}
            except TypeError:  # if we can't fetch the token contract metadata
                time.sleep(0.2)
            else:
                break

    t_a = time.time()
    minted_token = execute_transaction(deploy_mint, api_endpoint)
    t_b = time.time()

    logging.info("Succesfully minted master edition from {0} (time elapsed: {1})".format(contract_key, str(round(t_b - t_a, 4))))

    return minted_token


def new_article_token(contract_name, contract_description, mint_authority, metadata_url):
    nft_config = {"contract_name": contract_name,
                  "contract_symbol": "",
                  "mint_authority": mint_authority,
                  "metadata_url": metadata_url,
                  }

    return mint_master_edition(api_endpoint, core_account, core_priv_key, cipher, nft_config)
