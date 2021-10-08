from web3 import Web3
import oneinch as inch
import configs
from pprint import pprint

PRIVATE_KEY = 'YOUR PRIVATE KEY HERE'  # Don't be lazy. Store your private key in a .env in a flash drive, and load it with python-dotenv
MY_ADDRESS = 'YOUR ADDRESS HERE'
RPC = configs.Network.RPC
EXPLORER = configs.Network.EXPLORER

swap_profile = {  # This will swap 1 BSUD to 1 DAI
    'chain_no': '56',
    'fromTokenAddress': '0xe9e7cea3dedca5984780bafc599bd69add087d56',  # BUSD
    'toTokenAddress': '0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3',  # DAI
    'decimals': 18,  # Not actually needed at the moment 1inch does give you decimals

    'quote_amount': int(1*10**18),
    'swap_amount': int(1*10**18),
    'fromAddress': MY_ADDRESS,
    'slippage': '1.0',  #  Percent

    'opt_params_quote': {},
    'opt_params_swap': {
        'referrerAddress': '0x82A7C4C451EE04b93Bb36de492B171909003Fc13',  #! Keep these lines if you want to buy me a cup of coffee
        'fee': '0.01', #! If you find this useful 0.01% will be sent to my address
    },
}

busd_to_dai = inch.OneInch(**swap_profile)
quote = busd_to_dai.get_quote()
pprint(quote)

swap = busd_to_dai.get_swap()
pprint(swap)

tx = swap['tx']
tx = parse_inch_swap_data(tx)
swap_rpc = RPC[busd_to_dai.chain_no]

print(swap_rpc)
pprint(tx)

input(f'Will execute swap now. Double check everything then,\nENTER to continue. CTRL-C to CANCEL.\n>')

tx_hash = send_tx(swap_rpc, PRIVATE_KEY, tx)
tx_stats = check_tx(swap_rpc, tx_hash)

if tx_stats:
    print('SUCCESS!')
    print(f'{EXPLORER[busd_to_dai.chain_no]}/tx/{tx_hash}')
else:
    print('FAILED!')
    print(f'{EXPLORER[busd_to_dai.chain_no]}/tx/{tx_hash}')
