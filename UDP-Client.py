import ipaddress
import socket
import sys
import time

# 常量
TIMEOUT = 0.1  # 超时时间（秒）
TOTAL_PACKETS = 12  # 要发送的总包数
VERSION = 2  # 版本号
TYPE_REQUEST = 0  # 消息类型：请求
MAX_RETRANSMISSIONS = 2  # 最大重传次数

Buffer_Size = 1024  # 接收缓冲区大小
Seq_Bytes = 2  # 序号字节长度
Ver_Bytes = 1  # 版本字节长度
Type_Bytes = 1  # 类型字节长度
Length_Bytes = 3  # 长度字节长度
Time_Bytes = 8  # 时间字节长度
Payload_Bytes = 196  # 负载信息长度
Message_Bytes = 203  # 消息长度

# +-----------------+----------+--------+---------+-----------------------------+
# | sequence_number | version  |  type  |  length |            payload           |
# +-----------------+----------+--------+---------+-----------------------------+
# |       2B        |    1B    |   1B   |    3B   |            196B              |
# +-----------------+----------+--------+---------+-----------------------------+


def is_valid_ip(ip_str):
    """检查IP地址是否有效"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def is_valid_port(port):
    """检查端口号是否有效"""
    if port < '0' or port > '65535':
        return False
    return True


def establish_connection(ip, port, client_socket):
    """与服务器建立连接"""
    try:
        client_socket.settimeout(TIMEOUT)  # 设置超时时间
        handshake_message = "HELLO_SERVER"  # 握手消息
        client_socket.sendto(handshake_message.encode(), (ip, port))  # 发送握手
        response, server_address = client_socket.recvfrom(Buffer_Size)  # 接受响应
        if response.decode() == "HELLO_CLIENT":
            print("The connection to the server is successfully established")  # 与服务器建立连接成功
            return True
        else:
            print("Server response exception")  # 服务器响应异常
            return False
    except socket.timeout:
        print("Connection timeout")  # 连接超时
        return False
    except Exception:
        print(f"Connection error, please try again")  # 连接错误，请重试
        return False


def create_socket():
    """创建并配置UDP套接字"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建UDP套接字
    client_socket.settimeout(TIMEOUT)  # 设置套接字超时时间
    return client_socket


def send_packet(client_socket, sequence_number, ip, port):
    """构建并发送数据包"""
    payload = 'x' * Payload_Bytes  # 用'x'填充到200字节（消息类型：1字节， 报文长度：3字节）
    message = f"{sequence_number:02d}{VERSION}{TYPE_REQUEST}{Message_Bytes}{payload}"  # 构建报文
    client_socket.sendto(message.encode(), (ip, port))  # 发送报文


def receive_response(client_socket, start_time):
    """接收响应并计算RTT"""
    try:
        response, server = client_socket.recvfrom(Buffer_Size)  # 接收响应
        end_time = time.perf_counter()  # 记录接收时间
        rtt = (end_time - start_time) * 1000  # 计算RTT（毫秒）
        return response, rtt
    except socket.timeout:
        return None, None


def process_response(response, rtt, rtt_times, received_packets):
    """处理接收到的响应"""
    rtt_times.append(rtt)  # 记录RTT
    received_packets += 1  # 增加接收到的包数量
    parts = response.decode()  # 解析响应报文
    print(f"Successfully received response, Sequence No: {int(parts[0:Seq_Bytes])}, Version: {parts[Seq_Bytes:Seq_Bytes + Ver_Bytes]}, "
          f"Type: {parts[Seq_Bytes + Ver_Bytes:Seq_Bytes + Ver_Bytes + Type_Bytes]}, Length: {parts[Seq_Bytes + Ver_Bytes + Type_Bytes:Seq_Bytes + Ver_Bytes + Type_Bytes + Length_Bytes]}, "
          f"RTT: {rtt:.2f} ms, Server Time: {parts[Seq_Bytes + Ver_Bytes + Type_Bytes + Length_Bytes:Seq_Bytes + Ver_Bytes + Type_Bytes + Length_Bytes + Time_Bytes]}, "
          f"Server Payload: {parts[Seq_Bytes + Ver_Bytes + Type_Bytes + Length_Bytes + Time_Bytes:Message_Bytes]}")
    return received_packets


def print_summary(rtt_times, received_packets, total_retransmissions):
    """打印统计信息"""
    print(f"\nSummary:")
    print(f"Total packets sent: {TOTAL_PACKETS}")  # 发送到的udp packets数目
    print(f"Total packets received: {received_packets}")  # 接受到的udp packets数目
    print(f"Packet loss rate: {(1 - received_packets / TOTAL_PACKETS) * 100:.2f}%")  # 丢包率
    print(f"Total retransmissions: {total_retransmissions}")  # 重传次数
    if rtt_times:
        print(f"Min RTT: {min(rtt_times):.2f} ms")  # 最小RTT
        print(f"Max RTT: {max(rtt_times):.2f} ms")  # 最大RTT
        print(f"Avg RTT: {sum(rtt_times) / len(rtt_times):.2f} ms")  # 平均RTT


def main(ip, port, client_socket):
    """发送数据包并处理响应"""
    rtt_times = []  # 存储RTT的列表
    received_packets = 0  # 记录接收到的报文数量
    total_retransmissions = 0  # 记录重传次数

    for sequence_number in range(1, TOTAL_PACKETS + 1):  # 循环发送TOTAL_PACKETS个报文
        send_packet(client_socket, sequence_number, ip, port)  # 发送报文
        print(f"Send packet {sequence_number}, Version: {VERSION}, Type: {TYPE_REQUEST}, "
              f"Length: {Message_Bytes}")
        start_time = time.perf_counter()  # 记录发送报文的时间
        response, rtt = receive_response(client_socket, start_time)  # 接收响应并计算RTT
        if response:
            received_packets = process_response(response, rtt, rtt_times, received_packets)  # 处理响应
        else:
            retransmissions = 1  # 重传计数器

            while retransmissions <= MAX_RETRANSMISSIONS:
                print(f"Request timed out for packet {sequence_number}, "
                      f"retransmission underway {retransmissions} times...")
                send_packet(client_socket, sequence_number, ip, port)  # 重发数据包
                start_time = time.perf_counter()  # 重新记录发送时间
                response, rtt = receive_response(client_socket, start_time)  # 接收响应并计算RTT
                retransmissions += 1  # 增加重传计数器
                total_retransmissions += 1  # 增加总重传次数
                if response:
                    received_packets = process_response(response, rtt, rtt_times, received_packets)  # 处理响应
                    break

            if retransmissions > MAX_RETRANSMISSIONS:
                print(f"Packet {sequence_number} failed after {MAX_RETRANSMISSIONS} retransmissions")

    client_socket.sendto("close".encode(), (ip, port))  # 断开连接
    print_summary(rtt_times, received_packets, total_retransmissions)  # 打印统计信息
    response, server = client_socket.recvfrom(Buffer_Size)  # 接收响应
    if response.decode() == "close":
        client_socket.close()  # 关闭套接字


if __name__ == "__main__":
    # 检查命令行参数的数量是否为3（脚本名称、服务器IP地址、服务器端口号）
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <server_port>")
        sys.exit()

    server_ip = sys.argv[1]  # 获取服务器IP地址
    server_port = sys.argv[2]  # 获取服务器端口号

    # 检查IP地址是否合法
    if not is_valid_ip(server_ip):
        print("Invalid IP address")
        sys.exit()

    # 检查端口号是否合法
    if not is_valid_port(server_port):
        print("Invalid port")
        sys.exit()

    server_port = int(server_port)  # 将端口号转换为整数
    client_socket = create_socket()  # 创建并配置UDP套接字

    # 尝试与服务器建立连接，如果成功，则执行主函数
    if establish_connection(server_ip, server_port, client_socket):
        main(server_ip, server_port, client_socket)
