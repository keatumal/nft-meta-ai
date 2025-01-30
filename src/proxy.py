import socket
import socks
from src.config import get_env_settings, get_app_config

def setup_proxy():
    env = get_env_settings()
    config = get_app_config()

    if not config.general.get('use_proxy', False):
        return
    
    print(f'Turning on proxy {env.proxy_host}:{env.proxy_port}')
    socks.set_default_proxy(socks.SOCKS5, env.proxy_host, env.proxy_port,
                            username=env.proxy_user, password=env.proxy_password)
    socket.socket = socks.socksocket
