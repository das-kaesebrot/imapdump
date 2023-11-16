from imapclient.response_types import Envelope, Address
from urllib.parse import quote
    
def envelope_to_msg_title(envelope: Envelope) -> str:
    return f"{envelope.message_id.decode().strip('<').strip('>')} - {addr_to_str(envelope.sender)} - {envelope.date.isoformat()}"
    
def addr_to_str(addresses: tuple[Address]) -> str:
    if len(addresses) <= 0:
        return None
    
    addr = addresses[0]
    
    addr_str = f"{addr.mailbox.decode()}@{addr.host.decode()}"
    
    if addr.name:
        addr_str = f"{addr.name.decode()} <{addr_str}>"
    
    return addr_str