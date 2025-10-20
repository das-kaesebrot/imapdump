from imapclient.response_types import Envelope, Address

_max_length = 255 - len(".eml")


def envelope_to_msg_title(envelope: Envelope) -> str:
    ret_str_arr = []

    if envelope.subject:
        ret_str_arr.append(envelope.subject.decode())

    ret_str_arr.append(
        addr_to_str(envelope.sender if envelope.sender else envelope.from_)
    )

    if envelope.date:
        ret_str_arr.append(str(int(envelope.date.timestamp())))

    ret_str = " - ".join(ret_str_arr).replace("/", "").replace("\\", "")

    if not len(ret_str) > _max_length:
        return ret_str

    cutoff_length = len(ret_str) - _max_length
    ret_str_arr[0] = ret_str_arr[0][:-cutoff_length]

    return " - ".join(ret_str_arr).replace("/", "").replace("\\", "")


def addr_to_str(addresses: tuple[Address]) -> str:
    if not addresses or len(addresses) <= 0:
        return None

    addr = addresses[0]
    addr_str = ""

    if addr.mailbox:
        addr_str += addr.mailbox.decode()

    if addr.host:
        addr_str += f"@{addr.host.decode()}"

    if addr.name:
        addr_str = f"{addr.name.decode()} <{addr_str}>"

    return addr_str
