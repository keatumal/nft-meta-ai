from web3 import Web3
import requests
import datetime
import json
import os
import time
from typing import List, Dict, Optional
from web3.types import LogReceipt
from web3.datastructures import AttributeDict
from hexbytes import HexBytes

from src.config import get_env_settings, get_app_config
from src.log import log

class NFTMetadataFetcher:
    def __init__(
            self,
            network: str,
            contract_address: str,
            abi: list,
            mint_event_signature: str,
            first_id: int = 1,
            from_block: int = 0,
            use_cache: bool = True):
        networks = {
            'ethereum': f'https://mainnet.infura.io/v3',
            'zora': f'https://lb.drpc.org/ogrpc?network=zora&dkey=',
        }
        if network not in networks:
            raise ValueError(f'Unsupported network: {network}')
        
        env = get_env_settings()
        
        provider = networks[network].rstrip('/')
        if network == 'ethereum':
            provider += f'/{env.infura_api_key}'
        else:
            provider += env.drpc_api_key
        
        self.web3 = Web3(Web3.HTTPProvider(provider))
        if not self.web3.is_connected():
            raise ConnectionError('Failed to connect to the blockchain network.')
        
        self.contract = self.web3.eth.contract(address=self.web3.to_checksum_address(contract_address), abi=abi)
        
        try:
            self.collection_name = self.contract.functions.name().call()
        except Exception as e:
            raise RuntimeError(f'Failed to fetch collection name: {e}')
        
        try:
            self.next_token_id = self.contract.functions.nextTokenId().call()
        except Exception as e:
            raise RuntimeError(f'Failed to fetch nextTokenId: {e}')
        
        self.current_token_id = first_id

        self.network = network
        self.contract_address = contract_address
        self.event_signature = mint_event_signature
        self.first_id = first_id
        self.from_block = from_block
        self.use_cache = use_cache
        self.event_logs: Optional[List[Dict]] = None

        self.app_config = get_app_config()

    def __iter__(self):
        self.current_token_id = self.first_id
        return self

    def __next__(self):
        if self.current_token_id >= self.next_token_id:
            raise StopIteration
        
        token_data = self.fetch_metadata_for_token(self.current_token_id)
        self.current_token_id += 1
        return token_data

    def fetch_metadata_for_token(self, token_id: int) -> Dict:
        if token_id >= self.next_token_id:
            raise ValueError(f'Token ID {token_id} exceeds the maximum available ID {self.next_token_id - 1}.')
        if not self.event_logs:
            raise RuntimeError(f'Event logs are empty.')
        
        while True:
            try:
                token_uri = self.contract.functions.uri(token_id).call()
                metadata = self._fetch_ipfs_metadata(token_uri)
                mint_date = self._get_mint_date(token_id)
            
                return {
                    'token_id': token_id,
                    'name': metadata.get('name', 'N/A'),
                    'description': metadata.get('description', 'N/A'),
                    'image_url': self._convert_ipfs_to_http(metadata.get('image', 'N/A')),
                    'mint_date': mint_date,
                }
            except Exception as e:
                log.print(f'NFT metadata retrieval error: {e}')
                timeout = self.app_config.general.get('fetch_metadata_timeout', 60)
                log.print(f'Try again in {timeout} seconds')
                time.sleep(timeout)
        
    def fetch_event_logs(self):
        if self.event_logs:
            return
        
        if self.use_cache:
            cache_fname = self._get_cache_fname()
            if os.path.exists(cache_fname):
                print(f'Loading event logs from the cache: {cache_fname}')
                self.event_logs =  self._load_from_cache()
                return

        start_block = self.from_block
        latest_block = self.web3.eth.block_number
        all_logs = []
        
        event_signature_hash_bytes32 = '0x' + self.web3.keccak(text=self.event_signature).hex()
        zero_address_bytes32 = '0x' + '0' * 64

        print('Getting the logs of the mint events. This could take a while…')

        while True:
            logs = self.web3.eth.get_logs({
                'fromBlock': start_block,
                'toBlock': latest_block,
                'address': self.contract_address,
                # signature, operator, from, to
                'topics': [event_signature_hash_bytes32, None, zero_address_bytes32, None]
            })
            if len(logs) == 0:
                break
            all_logs.extend(logs)
            start_block = logs[-1]['blockNumber'] + 1
            if start_block > latest_block:
                break

        if len(all_logs) > 0:
            print(f'Received {len(all_logs)} records')
            if self.use_cache:
                self._save_to_cache(all_logs)
                print(f'The logs have been saved to the cache: {self._get_cache_fname()}')

            self.event_logs = all_logs
            return
        else:
            raise RuntimeError('No logs were found for the mint event')
        
    def _get_mint_date(self, token_id: int) -> Optional[datetime.datetime]:
        for log in self.event_logs:
            data = log['data']
            if isinstance(data, HexBytes):
                data = data.hex()
            data_token_id = int(data[:64], 16)
            if token_id != data_token_id:
                continue

            block = self.web3.eth.get_block(log['blockNumber'])
            timestamp = block['timestamp']
            mint_date = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
            return mint_date
        return None
        
    def _get_cache_fname(self) -> str:
        cache_dir = self.app_config.paths['cache']['event_logs']
        os.makedirs(cache_dir, exist_ok=True)
        cache_fname = os.path.join(cache_dir, f'{self.network}_{self.contract_address}.json')
        return cache_fname
        
    def _save_to_cache(self, logs: List[LogReceipt]):
        with open(self._get_cache_fname(), 'w') as f:
            serializable_logs = [self._to_serializable(log) for log in logs]
            json.dump(serializable_logs, f)

    def _load_from_cache(self) -> List[Dict]:
        with open(self._get_cache_fname(), 'r') as f:
            return json.load(f)
    
    def _to_serializable(self, value):
        if isinstance(value, AttributeDict):
            return {key: self._to_serializable(val) for key, val in value.items()}
        elif isinstance(value, HexBytes):
            return value.hex()
        elif isinstance(value, list):
            return [self._to_serializable(item) for item in value]
        else:
            return value

    @staticmethod
    def _fetch_ipfs_metadata(ipfs_url) -> Dict:
        if ipfs_url.startswith('ipfs://'):
            ipfs_url = ipfs_url.replace('ipfs://', 'https://ipfs.io/ipfs/')
        
        response = requests.get(ipfs_url)
        if response.status_code == 410:
            log.print(f'This URI no longer contains any data: {ipfs_url}')
            return {}
        response.raise_for_status()
        
        return response.json()

    @staticmethod
    def _convert_ipfs_to_http(ipfs_url):
        if ipfs_url.startswith('ipfs://'):
            return ipfs_url.replace('ipfs://', 'https://ipfs.io/ipfs/')
        return ipfs_url