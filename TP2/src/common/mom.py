import zmq
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, List
from common.utils import read_json

LOCALHOST = '127.0.0.1'
CONFIG_FILEPATH = 'middleware.json'
EOF_MSG_ID = 'EOF'
EOF_MSG = EOF_MSG_ID
MSG_SEP = ' '
MSG_DATA_JOINER = ','


@dataclass
class Message:
    id: str
    data: str


@dataclass
class Input:
    id: str
    data: Any


@dataclass
class Output:
    host: str
    msg_idx: int
    data: Any


Sendable = dict[str, Any]


class MOM:
    def __init__(self):
        self.__context: zmq.Context = zmq.Context()
        self.__read_config()

        # Init zmq pullers and pushers
        self.__init_puller()
        self.__init_pushers()

    def recv(self) -> Message:
        msg = self.__puller.recv_string()
        if msg == EOF_MSG:
            return Message(EOF_MSG_ID, None)

        return self.__parse_msg(msg)

    def send(self, result: Sendable):
        for output in self.__outputs:
            pusher = self.__pushers[output.host]
            serialized = MOM.__serialize(output.msg_idx, output.data, result)
            pusher.send_string(serialized)

    def send_eof(self):
        for output in self.__outputs:
            pusher = self.__pushers[output.host]
            pusher.send_string(EOF_MSG)

    # Private

    def __read_config(self):
        try:
            config = read_json(CONFIG_FILEPATH)

            # Common config
            self.__port = int(config['common']['port'])
            self.__protocol: str = config['common']['protocol']

            # Routing config
            raw_inputs = config['inputs']
            raw_outputs = config['outputs']
            self.__inputs = MOM.__parse_inputs(raw_inputs)
            self.__outputs = MOM.__parse_outputs(raw_outputs)
        except Exception:
            raise Exception('Invalid config file')

    def __addr(self, host: str):
        return f'{self.__protocol}://{host}:{self.__port}'

    def __init_puller(self):
        puller = self.__context.socket(zmq.PULL)
        addr = self.__addr(LOCALHOST)
        print(f'Binding puller to {addr}')
        puller.bind(addr)
        self.__puller = puller

    def __init_pushers(self):
        pushers: dict[str, zmq.Socket] = {}

        for output in self.__outputs:
            host = output.host
            if host in pushers:
                continue

            pusher = self.__context.socket(zmq.PUSH)
            addr = self.__addr(host)
            print(f'Connecting pusher to {addr}')
            pusher.connect(addr)
            pushers[host] = pusher

        self.__pushers = pushers

    def __parse_msg(self, raw_msg):
        msg_idx, raw_data = raw_msg.split(' ', 1)

        try:
            msg_id, MsgData = self.__inputs[int(msg_idx)]
        except Exception:
            raise Exception(f'Invalid message index received ({msg_idx})')

        try:
            msg_args = raw_data.split(',')
            data = MsgData(*msg_args)
        except Exception:
            raise Exception(
                'Could not parse message.'
                '\nExpected: {MsgData}'
                '\nReceived: {raw_data}'
            )

        return Message(msg_id, data)

    # Static

    @staticmethod
    def __parse_inputs(raw_inputs) -> List[Input]:
        inputs: List[Input] = []
        for raw_input in raw_inputs:
            msg_id = raw_input['id']
            raw_data = raw_input['data']
            MsgData = namedtuple(f'MsgData_{msg_id}', raw_data)
            input = Input(msg_id, MsgData)
            inputs.append(input)

        return inputs

    @staticmethod
    def __parse_outputs(raw_outputs) -> List[Output]:
        outputs: List[Output] = []
        for raw_output in raw_outputs:
            to_host = raw_output['to']
            msg_idx = int(raw_output['msg_idx'])
            raw_data = raw_output['data']
            MsgData = namedtuple(f'MsgData_{to_host}_{msg_idx}', raw_data)
            output = Output(to_host, msg_idx, MsgData)
            outputs.append(output)

        return outputs

    @staticmethod
    def __serialize(msg_idx: int, output_data, result: Sendable) -> str:
        output_values = [str(result[field]) for field in output_data._fields]
        data = MSG_DATA_JOINER.join(output_values)

        return f'{msg_idx}{MSG_SEP}{data}'
