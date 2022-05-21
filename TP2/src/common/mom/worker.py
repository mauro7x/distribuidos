import zmq
import logging
from collections import namedtuple
from typing import List, Dict
from common.utils import read_json
from common.mom.base import BaseMOM
from common.mom.types import Sendable, Message, Input, Output
import common.mom.constants as const


class WorkerMOM(BaseMOM):
    def __init__(self):
        super().__init__()

    def recv(self) -> Message:
        msg = self._puller.recv_string()
        if msg == const.EOF_MSG:
            return Message(const.EOF_MSG_ID, None)

        msg = self.__parse_msg(msg)
        logging.debug(f"Received: '{msg}'")
        return msg

    def send(self, result: Sendable):
        for output in self.__outputs:
            pusher = self.__pushers[output.host]
            serialized = WorkerMOM.__serialize(
                output.msg_idx, output.data, result)
            logging.debug(f"Sending '{serialized}' to {output.host}")
            pusher.send_string(serialized)

    def broadcast_eof(self):
        logging.info('Broadcasting EOF')
        for output in self.__outputs:
            pusher = self.__pushers[output.host]
            pusher.send_string(const.EOF_MSG)

    # Base class implementations

    def _parse_custom_config(self):
        logging.debug('Parsing worker configuration...')
        config = read_json(const.MIDDLEWARE_CONFIG_FILEPATH)
        raw_inputs = config['inputs']
        raw_outputs = config['outputs']
        self.__inputs = WorkerMOM.__parse_inputs(raw_inputs)
        self.__outputs = WorkerMOM.__parse_outputs(raw_outputs)
        logging.debug(
            'MOM worker configuration:'
            f'\nInputs: {self.__inputs}'
            f'\nOutputs: {self.__outputs}'
        )

    def _init_pushers(self):
        self.__pushers: Dict[str, zmq.Socket] = {}

        for output in self.__outputs:
            host = output.host
            if host in self.__pushers:
                continue

            pusher = self._context.socket(zmq.PUSH)
            addr = self._addr(host)
            logging.debug(f'Connecting pusher to {addr}')
            pusher.connect(addr)
            self.__pushers[host] = pusher

    # Private

    def __parse_msg(self, raw_msg):
        msg_idx, raw_data = raw_msg.split(const.MSG_SEP, 1)

        try:
            input = self.__inputs[int(msg_idx)]
            msg_id = input.id
            MsgData = input.data
        except Exception:
            error = f'Invalid message index received ({msg_idx})'
            logging.critical(error)
            raise Exception(error)

        try:
            msg_args = raw_data.split(const.MSG_DATA_JOINER)
            data = MsgData(*msg_args)
        except Exception:
            error = ('Could not parse message.'
                     f'\nExpected: {MsgData}'
                     f'\nReceived: {raw_data}')
            logging.critical(error)
            raise Exception(error)

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
        data = const.MSG_DATA_JOINER.join(output_values)

        return f'{msg_idx}{const.MSG_SEP}{data}'
