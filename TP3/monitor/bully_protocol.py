import logging

N_ID_BYTES = 1
ENDIANNESS = 'big'

FIXED_MESSAGE_LEN = 1
MAX_RECV_ATTEMPTS = 3


def __recv_all(s, expected_bytes, blocking):
    # TODO: use in common with cs_protocol
    s.setblocking(blocking)
    bytes = s.recv(expected_bytes)
    n_bytes = len(bytes)
    if not n_bytes:
        raise Exception("Peer disconnected")
    while len(bytes) < expected_bytes:
        bytes += s.recv(expected_bytes - len(bytes))
        if len(bytes) == n_bytes:
            raise Exception("Peer disconnected")
        else:
            n_bytes = len(bytes)
    return bytes


def send_msg(msg, s):
    # logging.debug("Sending msg {}".format(msg))
    return s.sendall(msg)


def send_id(id, s):
    # logging.debug("Sending id {}".format(id))
    from_id_bytes = id.to_bytes(N_ID_BYTES, ENDIANNESS)
    return s.sendall(from_id_bytes)


def recv_id(s, blocking=False):
    msg_bytes = __recv_all(s, N_ID_BYTES, blocking)
    id = int.from_bytes(msg_bytes, ENDIANNESS)
    # logging.debug("Received id {}".format(id))
    return id


def recv_msg(s, blocking=False):
    msg_byte = __recv_all(s, FIXED_MESSAGE_LEN, blocking)
    # logging.debug("Received msg {}".format(msg_byte))
    return msg_byte
