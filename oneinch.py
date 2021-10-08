from module.helpers import (
    get_with_retry
)
# import ssl
# import nest_asyncio
# nest_asyncio.apply()
import aiohttp
import asyncio
import urllib
import requests
from web3 import Web3

class OneInch:
    """
    Optional params see: https://docs.1inch.io/api/quote-swap
    """

    BASE_URL = 'https://api.1inch.exchange/v3.0'

    def __init__(
            self,
            chain_no,
            fromTokenAddress,
            toTokenAddress,
            decimals,
            quote_amount,
            swap_amount,
            fromAddress=None,
            slippage=None,
            opt_params_quote={},
            opt_params_swap={}
            ):

        # Input
        self.chain_no = chain_no
        self.fromTokenAddress = fromTokenAddress
        self.toTokenAddress = toTokenAddress
        self.decimals = decimals
        self.quote_amount = quote_amount
        self.swap_amount = swap_amount
        self.fromAddress = fromAddress
        self.slippage = slippage
        self.opt_params_quote = opt_params_quote
        self.opt_params_swap = opt_params_swap

        # Generated
        self.quote_raw = None
        self.swap_raw = None

    def url_factory(self, chain_no, endpoint, **kwparams) -> str:
        params = urllib.parse.urlencode(kwparams)
        return f'{self.BASE_URL}/{chain_no}/{endpoint}?{params}'

    @classmethod
    def healthcheck(cls, chain_no) -> bool:
        url = cls.url_factory(cls, chain_no, 'healthcheck')
        r = get_with_retry(url)
        if r.json()['status'] == 'OK':
            return True
        else:
            return False

    def get_quote_url(self) -> str:
        url = self.url_factory(
            self.chain_no,
            'quote',
            fromTokenAddress = self.fromTokenAddress,
            toTokenAddress = self.toTokenAddress,
            amount = self.quote_amount,
            **self.opt_params_quote,
            )

        return url

    def get_quote(self) -> dict:
        url = self.get_quote_url()
        r = get_with_retry(url)
        self.quote_raw = r.json()

        return self.quote_raw

    async def async_get_quote(self) -> dict:
        """
        Run this function with
        lst_get_quotes = [obj1.async_get_quote, obj2.async_get_quote, ...]
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(asyncio.gather(*lst_get_quotes))
        """
        url = self.get_quote_url()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.quote_raw = await response.json()

                return self.quote_raw

    def get_swap(self) -> dict:
        url = self.url_factory(
            self.chain_no,
            'swap',
            fromTokenAddress = self.fromTokenAddress,
            toTokenAddress = self.toTokenAddress,
            amount = self.swap_amount,
            fromAddress = self.fromAddress,
            slippage = self.slippage,
            **self.opt_params_swap,
            )
        # r = requests.get(url)
        r = get_with_retry(url)
        self.swap_raw = r.json()

        return self.swap_raw

    def __repr__(self):
        return f'{self.fromTokenAddress}>{self.toTokenAddress}'

    def __str__(self):
        return self.__repr__()


def check_oneinch_health(lst_chain_nos) -> bool:
    health = []
    print('Checking OneInch API health...')
    for chain_no in lst_chain_nos:
        is_healthy = OneInch.healthcheck(chain_no)
        if is_healthy:
            print(f'Chain: {chain_no} is healthy.')
        if not is_healthy:
            print(f'Chain: {chain_no} is BAD.')
        health.append(is_healthy)
    if all(health):
        # print(f'Chain: {lst_chain_nos} are healthy.')
        return True
    if not all(health):
        # print(f'At least one of the chains is/are BAD.')
        return False


def parse_inch_swap_data(tx):
    tx['from'] = web3.toChecksumAddress(tx['from'])
    tx['to'] = web3.toChecksumAddress(tx['to'])
    tx['value'] = int(tx['value'])
    tx['gas'] = int(tx['gas'])
    tx['gasPrice'] = int(tx['gasPrice'])

    return tx


def send_tx(RPC, PKEY, tx):
    web3 = Web3(Web3.HTTPProvider(RPC))

    if not web3.isConnected():
        raise ConnectionError(f'Couldn\'t connect to {RPC}')

    nonce = web3.eth.getTransactionCount(tx['from'])
    tx['nonce'] = nonce
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PKEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return tx_hash


def check_tx(RPC, tx_hash):
    web3 = Web3(Web3.HTTPProvider(RPC))
    max_tries = 20
    tx_status = -1

    last_ts = time.time()
    i = 0
    while True:

        if i >= max_tries:
            return False

        if last_ts + 3 > time.time():
            sleep(0.01)
            continue

        try:
            tx_status = web3.eth.getTransactionReceipt(tx_hash).status
            if tx_status:
                # log('Success!')
                return True
        except Exception as e:
            log('Waiting for tx status...')
            i += 1
            last_ts = time.time()
            continue

        i += 1
        last_ts = time.time()
