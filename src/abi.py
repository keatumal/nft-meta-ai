PURCHASED_EVENT_SIGNATURE = 'Purchased(address,address,uint256,uint256,uint256)'
TRANSFERSINGLE_EVENT_SIGNATURE = 'TransferSingle(address,address,address,uint256,uint256)'

ZORA1155_ABI = [
    {
        'constant': True,
        'inputs': [],
        'name': 'name',
        'outputs': [{'name': '', 'type': 'string'}],
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'nextTokenId',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [{'name': '_id', 'type': 'uint256'}],
        'name': 'uri',
        'outputs': [{'name': '', 'type': 'string'}],
        'type': 'function'
    }
]