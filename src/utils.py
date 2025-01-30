import datetime
import os
import base64
import requests
import time
from PIL import Image
from io import BytesIO

from typing import Optional, List
from sqlalchemy.orm import Session
from src.db import NFTMetadata
from src.log import log
from src.config import get_app_config

def add_ntf_to_db(
        session: Session,
        network: str,
        contract_address: str,
        collection_name: str,
        token_id: int,
        token_name: Optional[str],
        description: Optional[str],
        image_url: Optional[str],
        mint_date: Optional[datetime.datetime],
        ai_image_description: Optional[str]):
    
    new_nft = NFTMetadata(
        network_name=network,
        contract_address=contract_address,
        collection_name=collection_name,
        token_id=token_id,
        token_name=token_name,
        description=description,
        image_url=image_url,
        mint_date=mint_date,
        ai_image_description=ai_image_description
    )
    
    session.add(new_nft)
    session.commit()

def download_image(image_url: str, directory: str, resolution: List[int]) -> str:
    hash = image_url.rstrip('/').split('/')[-1]
    image_path = os.path.join(directory, f'{hash}.png')
    if not os.path.exists(image_path):
        log.print(f'Downloading the image: {image_url}')

        while True:
            response = requests.get(image_url)
            if response.status_code != 200:
                log.print(f'Failed to download image. Status code: {response.status_code}')

                config = get_app_config()
                timeout = config.general.get('download_image_timeout', 5)
                log.print(f'Try again in {timeout} seconds')
                time.sleep(timeout)
                continue
            break

        if not os.path.exists(directory):
            os.makedirs(directory)

        image = Image.open(BytesIO(response.content))

        # Resize the image
        log.print(f'Converting the image to the maximum size of {resolution[0]}x{resolution[1]}')
        max_size = (resolution[0], resolution[1])
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        image.save(image_path)
    else:
        log.print(f'Using a saved image: {image_path}')

    with open(image_path, 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return str(base64_image)