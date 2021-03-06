from LoginUI import *
from RegisterUI import *
from MainUI import *
from PySide.QtGui import *
from User import *
import socket
import pickle
import sys
import threading

# Main UI / Client
class UImanager(QMainWindow):
    def __init__(self, host, port=9999):
        #Main UI set up
        QMainWindow.__init__(self, None)
        self.setMinimumSize(1280, 720)
        self.setWindowTitle("MBM v.0")
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap("Images/background.png")))
        self.setPalette(palette)

        # Init main Widget
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        login_widget = LoginUI(self)
        self.central_widget.addWidget(login_widget)

        # Init state attributes
        self.state = "offline"

        #add widget
        self.login_widget = LoginUI(self)
        self.main_widget = MainUI(self)
        self.register_widget = RegisterUI(self)
        self.central_widget.addWidget(self.login_widget)
        self.central_widget.addWidget(self.main_widget)
        self.central_widget.addWidget(self.register_widget)

        # Init socket part
        self.isServerOnline = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connect()

        if self.isServerOnline:
            # Init user
            self.user = None
            self.userThread = threading.Thread(target=self.waitingForUser, args=[])
            self.userThread.setDaemon(True)
            self.userThread.start()

        self.thread = threading.Thread(target=self.listen, args=[])
        self.thread.setDaemon(True)

    # Change page signal (send from log in UI page)
    def changePageLoginSection(self, signal = None, user = None):
        if signal == "login":
            self.state = "waiting"
            self.send('logIn', user)
            # Waiting for user to login
            while self.state == "waiting":
                pass
            if self.state == "online":
                self.centralWidget().setCurrentWidget(self.main_widget)
                palette = QPalette()
                palette.setBrush(QPalette.Background, QBrush(QPixmap("Images/background2.png")))
                self.setPalette(palette)

        elif signal == "register":
            self.centralWidget().setCurrentWidget(self.register_widget)

    # Change Page signal (send from register UI page)
    def changePageRegisterSection(self, signal = None, user = None):
        if signal == "register_confirm":
            self.send('register', user)
            self.centralWidget().setCurrentWidget(self.login_widget)
        elif signal == "back":
            self.centralWidget().setCurrentWidget(self.login_widget)

    # Recieve task and object before logged in
    def waitingForUser(self):
        print('Waiting for User')
        while True:
            task = self.socket.recv(1024).decode('ascii')
            if task == '':
                break
            try:
                obj = pickle.loads(self.socket.recv(4096))
                self.state = "waiting"
                # check if the user logged in successfully
                if task == 'logIn' and type(obj) == User:
                    self.user = obj
                    print("Initialize user successfully")
                    self.state = "online"
                    break
                # check if the user registered successfully
                elif task == 'register' and obj is True:
                    print("Registered successfully")
                else:
                    print("Invalid Username or Password")
                    self.state = "offline"
                    print(obj)
            except EOFError as e:
                print(e)
        # Start listening for the server
        self.thread.start()

    # Recieve task and object after logged in
    def listen(self):
        while True:
            print('listening')
            task = self.socket.recv(1024).decode('ascii')
            if task == '':
                break
            try:
                obj = pickle.loads(self.socket.recv(4096))
                #do sth. with the object
            except EOFError as e:
                print(e)

    # Connect to the server
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            msg = self.socket.recv(1024)
            print(msg.decode('ascii'))
            self.isServerOnline = True
        except ConnectionRefusedError:
            print("The server is currently offline.")

    # Send task and object
    def send(self, task, obj):
        self.socket.send(task.encode('ascii'))
        obj = pickle.dumps(obj)
        self.socket.send(obj)

    # Close the socket connection
    def close(self):
        self.socket.close()

def main():
    app = QApplication(sys.argv)
    ui = UImanager(socket.gethostname())
    ui.show()
    app.exec_()

if __name__ == "__main__":
    main()