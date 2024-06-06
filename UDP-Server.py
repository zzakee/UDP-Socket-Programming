import socket
import random
import time
import threading

HOST = '127.0.0.1'  # 服务器IP地址
PORT = 12345  # 服务器端口号
LOSS_RATE = 0.5  # 50%的丢包概率
VERSION = 2  # 版本号
TYPE_RESPONSE = 1  # 消息类型：响应

Buffer_Size = 1024  # 接收缓冲区大小
Seq_Bytes = 2  # 序号字节长度
Ver_Bytes = 1  # 版本字节长度
Type_Bytes = 1  # 类型字节长度
Length_Bytes = 3  # 长度字节长度
Time_Bytes = 8  # 时间字节长度
Payload_Bytes = 188  # 负载信息长度
Message_Bytes = 203  # 消息长度


# +-----------------+----------+--------+---------+-----------------+-----------------------+
# | sequence_number | version  |  type  |  length |   current_time  |        payload        |
# +-----------------+----------+--------+---------+-----------------+-----------------------+
# |       2B        |    1B    |   1B   |    3B   |       8B        |         188B          |
# +-----------------+----------+--------+---------+-----------------+-----------------------+

def handle_client(server_socket):
    """建立连接"""
    while True:
        try:
            request, client_address = server_socket.recvfrom(Buffer_Size)  # 接收客户端消息
            if request.decode() == "HELLO_SERVER":  # 检查握手消息
                server_socket.sendto("HELLO_CLIENT".encode(), client_address)  # 发送握手响应
                print(f"A connection is successfully established with {client_address}")  # 连接成功
                return True, client_address
        except Exception as e:
            print(f"error: {e}")  # 处理异常


def run_client(server_socket):
    """处理客户端的请求"""
    flag, client_address = handle_client(server_socket)
    if flag:  # 处理客户端的初始连接
        while True:  # 持续运行
            try:
                request, address = server_socket.recvfrom(Buffer_Size)  # 接收数据报文
                if request.decode() == "close":  # 检查关闭连接消息
                    server_socket.sendto("close".encode(), client_address)
                    print(f"Client {client_address} is closed")  # 打印关闭连接消息
                    break
                if address == client_address:
                    parts = request.decode()  # 解析数据报文
                    seq_no = int(parts[0:Seq_Bytes])  # 获取序列号
                    current_time = time.strftime("%H-%M-%S", time.localtime())  # 获取当前时间
                    response_message = construct_response_message(seq_no, current_time)  # 构建响应报文
                    if random.random() >= LOSS_RATE:  # 决定是否响应
                        server_socket.sendto(response_message.encode(), address)  # 发送响应报文
                        print(f"Successfully received the packet {seq_no}, time: {current_time}")  # 打印成功接收的报文
                    else:
                        print(f"Packet {seq_no} is lost")  # 丢包
            except Exception as e:  # 处理异常
                print(f"error: {e}")


def create_socket():
    """创建并配置UDP套接字"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建UDP套接字
    server_socket.bind((HOST, PORT))  # 绑定套接字到指定的IP和端口
    return server_socket


def construct_response_message(seq_no, current_time):
    """构建响应消息"""
    server_payload = 'x' * Payload_Bytes  # 构建负载数据
    response_message = (f"{seq_no:02d}{VERSION}{TYPE_RESPONSE}{Message_Bytes}"
                        f"{current_time}{server_payload}")  # 构建响应消息
    return response_message


def main():
    """启动服务器并处理客户端连接"""
    server_socket = create_socket()  # 创建并配置UDP套接字
    print(f"Start Server on ({HOST}, {PORT})")  # 打印服务器监听信息

    try:
        while True:  # 持续运行服务器
            thread = threading.Thread(target=run_client(server_socket))  # 创建新线程处理客户端
            thread.daemon = True  # 设置守护线程
            thread.start()  # 启动线程
    except Exception as e:
        print(f"error: {e}")  # 处理异常
    finally:
        server_socket.close()  # 关闭套接字


if __name__ == "__main__":
    main()
