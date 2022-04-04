import socket
import logging
import signal


class Server:
    def __init__(self, port, listen_backlog, timeout):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.settimeout(timeout)
        self._closed = False
        signal.signal(signal.SIGINT, self.__handle_close_signal)
        signal.signal(signal.SIGTERM, self.__handle_close_signal)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again

        Accept is done in a non-blocking way to allow exit gracefully
        Server will check if there are new connections to be 
        accepted once everytimeout, but checking also if server
        has been closed. In that case, it will close gracefully.
        """

        ACCEPTING_MSG = "Proceed to accept new connections"

        logging.info(ACCEPTING_MSG)
        while not self._closed:
            client_sock = self.__accept_or_timeout()
            if client_sock:
                self.__handle_client_connection(client_sock)
                logging.info(ACCEPTING_MSG)

        self.__close_gracefully()

    def __accept_or_timeout(self):
        """
        Try to accept a new connection.
        If socket timeouts before a client gets to connect,
        will return None.
        """

        try:
            return self.__accept_new_connection()
        except socket.timeout:
            return

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            client_sock.send(
                "Your Message has been received: {}\n".format(msg).encode('utf-8'))
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made,
        or until timeout is reached:
        - In case of timeout, proper exception will be raised.
        - In case of connection, it is printed and returned.
        """

        # Connection arrived
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c

    def __handle_close_signal(self, *args):
        """
        Handles close signal (SIGINT, SIGTERM)

        Function will flag server as closed, allowing it 
        to exit gracefully when detected.
        """

        self._closed = True

    def __close_gracefully(self):
        """
        Shutdowns and closes server socket to free resources.
        """

        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()
