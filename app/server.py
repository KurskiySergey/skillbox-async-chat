#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    max_message_history = 10

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if self.server.clients.get(login) is None:
                    self.login = login
                    self.send_message(f"Подключился к сессии")
                    self.server.clients[login] = self
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.write_history()

                else:
                    self.transport.write("В данной сессии уже существует данный логин. "
                                         "Введите другой\n".encode())
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
            self.transport = transport
            self.transport.write("Для входа в чат введите"
                                 " login:(Ваш логин)\n".encode())
            print("Пришел новый клиент")


    def connection_lost(self, exception):
        self.server.clients.pop(self.login)
        self.send_message(f"вышел из чата")
        print(f"Клиент {self.login} вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        self.save_message(message)
        for login, user in self.server.clients.items():
            user.transport.write(message.encode())

    def write_history(self):

        self.transport.write(f"Последние {self.max_message_history} сообщений\n".encode())
        for message in self.server.messages:
            self.transport.write(f"{message}\n".encode())

    def save_message(self, message: str):

        if len(self.server.messages) > self.max_message_history:
            self.server.messages.pop(0)
        self.server.messages.append(message)


class Server:
    clients: dict
    messages: list

    def __init__(self):
        self.clients = {}
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
