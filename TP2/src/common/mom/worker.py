import logging
from collections import namedtuple
from typing import List, Dict
from common.utils import read_json
from common.mom.base import BaseMOM
from common.mom.types import \
    Sendable, Input, Output, RawDataMessage, DataMessage
from common.mom.transport.batching import BatchingPusher as Pusher
import common.mom.constants as const


LOG_NAME = 'WorkerMOM'


class WorkerMOM(BaseMOM):
    def __init__(self):
        logging.debug(f'[{LOG_NAME}] Initializing')
        super().__init__()
        logging.debug(f'[{LOG_NAME}] Initialized')

    def __del__(self):
        super().__del__()

    def send_data_row(self, result: Sendable):
        for output in self.__csv_outputs:
            pusher = self.__pushers[output.host]
            serialized = self.__serialize(
                output.msg_idx, output.data, result)
            logging.debug(
                f'[{LOG_NAME}] Sending "{serialized}" to {output.host}')
            pusher.send_data_row(serialized)

    def send_bytes(self, data: bytes):
        for output in self.__bytearray_outputs:
            pusher = self.__pushers[output.host]
            logging.debug(
                f'[{LOG_NAME}] Sending {len(data)} bytes'
                f' (binary) to {output.host}'
            )
            pusher.send_bytes(data)

    def broadcast_eof(self):
        logging.debug(f'[{LOG_NAME}] Broadcasting EOF')
        for pusher in self.__pushers.values():
            pusher.send_eof()

    # Base class implementations

    def recv(self) -> DataMessage:
        msg = self._recv_data_msg()
        if msg:
            return self.__parse_msg(msg.data)

    def _parse_custom_config(self):
        logging.debug(f'[{LOG_NAME}] Parsing configuration...')
        config = read_json(const.MIDDLEWARE_CONFIG_FILEPATH)
        raw_inputs = config['inputs']
        raw_outputs = config['outputs']
        self.__parse_inputs(raw_inputs)
        self.__parse_outputs(raw_outputs)

        pretty_inputs = list(map(lambda x: x.id, self.__inputs))
        outputs = [*self.__csv_outputs, *self.__bytearray_outputs]
        pretty_outputs = list(map(
            lambda x: (x.host, x.msg_idx) if x.msg_idx else (x.host, 'bytes'),
            outputs
        ))
        logging.debug(
            f'[{LOG_NAME}] Configuration:'
            f'\nInputs: {pretty_inputs}'
            f'\nOutputs: {pretty_outputs}'
        )

    def _init_pushers(self, _):
        self.__pushers: Dict[str, Pusher] = {}

        csv_hosts = [output.host for output in self.__csv_outputs]
        bytearray_hosts = [output.host for output in self.__bytearray_outputs]
        hosts = set([*csv_hosts, *bytearray_hosts])

        for host in hosts:
            if host in self.__pushers:
                continue

            pusher = Pusher(self._context, self._protocol, self._batch_size)
            pusher.connect(host, self._port)
            self.__pushers[host] = pusher

    def _close_pushers(self):
        for pusher in self.__pushers.values():
            pusher.close()

    # Private

    def __parse_inputs(self, raw_inputs) -> List[Input]:
        self.__inputs: List[Input] = []
        for raw_input in raw_inputs:
            msg_id = raw_input['id']
            raw_data = raw_input['data']
            MsgData = namedtuple(f'MsgData_{msg_id}', raw_data)
            input = Input(msg_id, MsgData)
            self.__inputs.append(input)

    def __parse_outputs(self, raw_outputs):
        self.__csv_outputs: List[Output] = []
        self.__bytearray_outputs: List[Output] = []

        for raw_output in raw_outputs:
            to_host = raw_output['to']
            msg_idx = raw_output.get('msg_idx')
            data = raw_output['data']

            if isinstance(data, str):  # BYTEARRAY
                output = Output(to_host, msg_idx, data)
                self.__bytearray_outputs.append(output)
            elif isinstance(data, list):  # CSV
                msg_idx = int(msg_idx)
                MsgData = namedtuple(f'MsgData_{to_host}_{msg_idx}', data)
                output = Output(to_host, msg_idx, MsgData)
                self.__csv_outputs.append(output)
            else:
                raise Exception(f'Invalid output data: {data}')

    def __parse_msg(self, msg: RawDataMessage) -> DataMessage:
        try:
            input = self.__inputs[msg.idx]
            msg_id = input.id
            MsgData = input.data
        except Exception:
            raise Exception(f'Invalid message index received ({msg.idx})')

        try:
            msg_args = self._unpack(msg.data)
            data = MsgData(*msg_args)
        except Exception:
            expected = MsgData._fields
            raise Exception('Could not parse message'
                            f'\nExpected: {expected} '
                            f'(len: {len(expected)})'
                            f'\nReceived: {msg.data}')

        return DataMessage(msg_id, data)

    def __serialize(self, msg_idx: int, output_data, result: Sendable) -> str:
        output_values = [str(result[field]) for field in output_data._fields]
        data = self._pack(output_values)

        return f'{msg_idx}{const.MSG_SEP}{data}'
