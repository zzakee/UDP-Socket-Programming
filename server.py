import socket
import threading

HOST = '127.0.0.1'  # 服务器IP地址
PORT = 12345  # 服务器端口号
Buffer_Size = 1024  # 接收缓冲区大小
Type_Bytes = 2  # 类型字节长度
N_Bytes = 4  # 块数字节长度
Length_Bytes = 4  # 长度字节长度


def reverse(string):
    """反转字符串并返回结果"""
    return string[::-1]


def create_socket():
    """创建并配置TCP套接字"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
    server_socket.bind((HOST, PORT))  # 绑定套接字到指定的IP和端口
    return server_socket


def handle_message(message):
    """根据消息类型解析并处理消息"""
    type = int(message[0:Type_Bytes])  # 从消息中解析出消息类型
    if type == 1:
        N = int(message[Type_Bytes:Type_Bytes + N_Bytes])  # 解析出块的数量
        return type, N
    elif type == 2:
        return type  # 返回类型2，表示同意处理
    elif type == 3:
        length = int(message[Type_Bytes:Type_Bytes+Length_Bytes])  # 解析出数据的长度
        data = message[Type_Bytes+Length_Bytes:Type_Bytes+Length_Bytes+length]  # 解析出数据本身
        return type, length, data
    elif type == 4:
        length = int(message[Type_Bytes:Type_Bytes + Length_Bytes])  # 解析出反转数据的长度
        reverse_data = message[Type_Bytes + Length_Bytes:Type_Bytes + Length_Bytes + length]  # 解析出反转后的数据
        return type, length, reverse_data
    else:
        raise Exception("error : Invalid message type")  # 异常处理，未知的消息类型


def run_client(sock, addr):
    """为每个连接的客户端创建一个线程来处理请求"""
    print('Connected with client : ', addr)  # 打印连接的客户端地址
    request = sock.recv(Buffer_Size).decode()  # 接收来自客户端的请求
    details = handle_message(request)  # 处理接收到的消息

    if details[0] != 1:
        sock.close()  # 如果不是类型1的消息，则关闭连接
        print('Close the connection with client : ', addr)
        return
    N = details[1]

    agree = "02"  # 发送类型2的消息，表示同意处理
    sock.send(agree.encode())

    for i in range(N):  # 循环接收和发送N次数据
        request = sock.recv(Buffer_Size).decode()
        details = handle_message(request)
        if details[0] == 3:
            data = reverse(details[2])  # 反转接收到的数据
            response = "04" + str(len(data)).zfill(Length_Bytes) + data  # 组成类型4的消息，并发送
            sock.send(response.encode())
        else:
            sock.close()  # 如果接收到的不是类型3的消息，则关闭连接
            print('Close the connection with client : ', addr)
            return


def main():
    server_socket = create_socket()  # 创建套接字
    server_socket.listen(5)  # 开始监听连接请求
    try:
        while True:  # 持续运行服务器
            socket, address = server_socket.accept()  # 接受一个新的连接
            thread = threading.Thread(target=run_client, args=(socket, address))  # 为每个新连接创建一个线程
            thread.start()  # 启动线程

    except Exception as e:
        print(f"error: {e}")  # 处理异常
    finally:
        server_socket.close()  # 关闭套接字


if __name__ == "__main__":
    main()
