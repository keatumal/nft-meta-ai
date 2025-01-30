from typing import Optional

class Log:
    def __init__(self, overwrite_width: int = 80, address_chars_num: int = 4):
        self.network = 'N/A'
        self.contract_address = 'N/A'
        self.token_id = 0
        self.token_last_id = 0

        self.overwrite_width = overwrite_width
        self.address_chars_num = address_chars_num

    def format_address(self, address: str) -> str:
        if address.startswith('0x'):
            address = address[2:]
        if len(address) < 10:
            return address
        result = address[:self.address_chars_num] + '…' + address[-self.address_chars_num:]
        return result
    
    def set_params(
            self,
            network: Optional[str] = None,
            contract_address: Optional[str] = None,
            token_id: Optional[int] = None,
            token_last_id: Optional[int] = None):
        if network:
            self.network = network
        if contract_address:
            self.contract_address = contract_address
        if token_id:
            self.token_id = token_id
        if token_last_id:
            self.token_last_id = token_last_id

    def print(
            self,
            msg: str,
            network: Optional[str] = None,
            contract_address: Optional[str] = None,
            token_id: Optional[int] = None,
            token_last_id: Optional[int] = None,
            overwrite: bool = False):
        
        if not network:
            network = self.network
        if not contract_address:
            contract_address = self.contract_address
        if not token_id:
            token_id = self.token_id
        if not token_last_id:
            token_last_id = self.token_last_id

        output = '[' + self.network + ' ' + self.format_address(self.contract_address) + \
            ' NFT ' + str(self.token_id) + '/' + str(self.token_last_id) + '] ' + msg
        if overwrite:
            if len(output) < self.overwrite_width:
                output += ' ' * (self.overwrite_width - len(output))
            print(output, end='\r', flush=True)
        else:
            print(output)

log = Log()