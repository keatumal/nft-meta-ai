from src.nft import NFTMetadataFetcher
from src.gpt import OpenAIImageToText

from src.proxy import setup_proxy
from src.config import get_app_config, get_env_settings
from src.db import DatabaseManager, NFTMetadata

from src.abi import ZORA1155_ABI, TRANSFERSINGLE_EVENT_SIGNATURE

from src.log import log
from src.utils import download_image, add_ntf_to_db

config = get_app_config()
env = get_env_settings()

setup_proxy()

print('Initializing the database')
db_manager = DatabaseManager(env.db_uri)
session = db_manager.get_session()

chains = config.blockchains

for chain_name in chains:
    for contract in chains[chain_name]['contracts']:
        contract_address = contract['address']
        from_block = contract.get('from_block', 0)
        first_nft_id = contract.get('first_id', 1)

        print(f'The event log search will be from block #{from_block} for the `{chain_name}` blockchain')

        nft_fetcher = NFTMetadataFetcher(
            network=chain_name,
            contract_address=contract_address,
            abi=ZORA1155_ABI,
            mint_event_signature=TRANSFERSINGLE_EVENT_SIGNATURE,
            from_block=from_block,
            first_id=first_nft_id
        )

        nft_fetcher.fetch_event_logs()

        for token_id in range(first_nft_id, nft_fetcher.next_token_id):
            log.set_params(network=chain_name, contract_address=contract_address,
                           token_id=token_id, token_last_id=nft_fetcher.next_token_id - 1)
            nft_row = session.query(NFTMetadata).filter(
                NFTMetadata.network_name == chain_name,
                NFTMetadata.contract_address == contract_address,
                NFTMetadata.token_id == token_id
            ).first()

            fetch_metadata = False
            generate_description = False
            fetch_success = False
            ai_desc = None

            if nft_row:
                if not nft_row.ai_image_description or \
                    len(nft_row.ai_image_description) < config.openai.get('description_min_len', 100):
                    generate_description = True
                if not nft_row.collection_name or not nft_row.token_name or not \
                    nft_row.description or not nft_row.image_url:
                    fetch_metadata = True
            else:
                fetch_metadata = True
                generate_description = True

            if fetch_metadata:
                log.print('Getting NFT metadata')
                token = nft_fetcher.fetch_metadata_for_token(token_id)

                if 'error' in token:
                    log.print(f"Can't get the metadata: {token['error']}")
                else:
                    fetch_success = True

            if generate_description and fetch_success:
                log.print(f'Generating a description via `{config.openai["model"]}` model')
                gpt = OpenAIImageToText(env.openai_api_key, config.openai['model'])
                image_base64 = download_image(token['image_url'],
                                              config.paths['nft_images_dir'],
                                              config.openai.get('image_resolution', [512, 512]))
                gpt_resp = gpt.get_text_from_image(image_base64, "image/png", config.openai['prompt'])
                if 'error' in gpt_resp:
                    log.print(f'OpenAI API Error: {gpt_resp["error"]}')
                else:
                    ai_desc = gpt_resp['response']

            if nft_row and fetch_success:
                    nft_row.network_name = chain_name
                    nft_row.contract_address = contract_address
                    nft_row.collection_name = nft_fetcher.collection_name
                    nft_row.token_id = token['token_id']
                    nft_row.token_name = token['name']
                    nft_row.description = token['description']
                    nft_row.image_url = token['image_url']
                    nft_row.mint_date = token['mint_date']
                    session.commit()
            elif not nft_row and fetch_success:
                add_ntf_to_db(
                    session,
                    network=chain_name,
                    contract_address=contract_address,
                    collection_name=nft_fetcher.collection_name,
                    token_id=token_id,
                    token_name=token['name'],
                    description=token['description'],
                    image_url=token['image_url'],
                    mint_date=token['mint_date'],
                    ai_image_description=ai_desc
                )
            if nft_row and ai_desc:
                nft_row.ai_image_description = ai_desc
                session.commit()

            if nft_row and not fetch_metadata and not generate_description:
                log.print('Skipping')

session.close()
print('\nDone')