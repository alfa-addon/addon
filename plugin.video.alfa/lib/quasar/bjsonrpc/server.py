"""
    bjson/server.py

    Asynchronous Bidirectional JSON-RPC protocol implementation over TCP/IP

    Copyright (c) 2010 David Martinez Marti
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
    3. Neither the name of copyright holders nor the names of its
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
    TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
    PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL COPYRIGHT HOLDERS OR CONTRIBUTORS
    BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

"""
import xbmc
import socket
import select

from bjsonrpc.connection import Connection
from bjsonrpc.exceptions import EofError

class Server(object):
    """
        Handles a listening socket and automatically accepts incoming
        connections. It will create a *bjsonrpc.connection.Connection* for
        each socket connected to it.

        Use the *Server.serve()* method to start accepting connections.

        Parameters:

        **lstsck**
            Listening socket to watch for incoming connections. Must be an instance
            of *socket.socket* or something compatible, and must to be already
            listening for new connections in the desired port.

        **handler_factory**
            Class (object type) to instantiate to publish methods for incoming
            connections. Should be an inherited class of *bjsonrpc.handlers.BaseHandler*

    """
    def __init__(self, lstsck, handler_factory):
        self._lstsck = lstsck
        self._handler = handler_factory
        self._debug_socket = False
        self._debug_dispatch = False
        self._serve = True

    def stop(self):
        """
            Tells the server that it should stop. Useful in multithread apps.
            Once stopped, call again to *serve()* to start the server loop again.
        """
        self._serve = False

    def debug_socket(self, value=None):
        """
            Sets or retrieves the internal debug_socket value.

            When is set to true, each new connection will have it set to true,
            and every data sent or received by the socket will be printed to
            stdout.

            By default is set to *False*
        """
        retval = self._debug_socket
        if type(value) is bool:
            self._debug_socket = value

        return retval

    def debug_dispatch(self, value=None):
        """
            Sets or retrieves the internal debug_dispatch value.

            When is set to true, each new connection will have it set to true,
            and every error produced by client connections will be printed to
            stdout.

            By default is set to *False*
        """
        ret = self._debug_dispatch
        if type(value) is bool:
            self._debug_dispatch = value

        return ret

    def serve(self):
        """
            Starts the forever-serving loop. This function only exits when an
            Exception is raised inside, by unexpected error, KeyboardInterrput,
            etc.

            It is coded using *select.select* function, and it is capable to
            serve to an unlimited amount of connections at same time
            without using threading.
        """
        self._serve = True
        try:
            sockets = []
            connections = []
            connidx = {}
            monitor_abort = xbmc.Monitor()  # For Kodi >= 14
            while not monitor_abort.abortRequested():
                try:
                    ready_to_read = select.select(
                        [self._lstsck] + sockets,  # read
                        [], [],  # write, errors
                        1  # timeout
                    )[0]
                except Exception:
                    # Probably a socket is no longer valid.
                    a = self._lstsck.fileno()  # if this is not valid, raise Exception, exit.
                    newsockets = []
                    for sck in sockets:
                        try:
                            a = sck.fileno()  # NOQA
                            h = sck.getpeername()  # NOQA
                        except Exception:
                            continue
                        newsockets.append(sck)
                    sockets[:] = newsockets
                    continue
                if not ready_to_read:
                    continue

                if self._lstsck in ready_to_read:
                    clientsck, clientaddr = self._lstsck.accept()
                    sockets.append(clientsck)

                    conn = Connection(
                        sck=clientsck, address=clientaddr,
                        handler_factory=self._handler
                    )
                    connidx[clientsck.fileno()] = conn
                    conn._debug_socket = self._debug_socket
                    conn._debug_dispatch = self._debug_socket
                    # conn.internal_error_callback = self.

                    connections.append(conn)

                for sck in ready_to_read:
                    fileno = sck.fileno()
                    if fileno not in connidx:
                        continue

                    conn = connidx[fileno]
                    try:
                        conn.dispatch_until_empty()
                    except EofError:
                        conn.close()
                        sockets.remove(conn.socket)
                        connections.remove(conn)
                        # print "Closing client conn."

        finally:
            for conn in connections:
                conn.close()
            try:
                self._lstsck.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self._lstsck.close()
            except Exception:
                pass

    @property
    def socket(self):
        """
            public property that holds the internal listener socket used.
        """
        return self._lstsck
