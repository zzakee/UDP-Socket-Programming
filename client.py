import ipaddress
import random
import socket
import sys

FILE_IN = 'in.txt'
FILE_OUT = 'out.txt'
Buffer_Size = 1024  # 接收缓冲区大小
Type_Bytes = 2  # 类型字节长度
N_Bytes = 4  # 块数字节长度
Length_Bytes = 4  # 长度字节长度

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


def is_valid_range(lmin,lmax):
    """检查给定的范围是否有效（lmin < lmax 并且都是数字）。"""
    if lmin < lmax and lmin.isdigit() and lmax.isdigit():
        return True
    return False


def create_socket():
    """创建并配置TCP套接字"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
    return client_socket


def get_file_message(file_path):
    """从文件中读取并返回内容。"""
    with open(file_path, 'r') as f:
        message = f.read()
        return message


def update_file_message(file_path, messages):
    """将反转后的信息更新到输出文件中。"""
    with open(file_path, 'w') as f:
        for message in reversed(messages):
            f.write(message)


def get_send_message(data, lmin, lmax):
    """根据指定的范围随机分割数据。"""
    info = []
    while len(data) > 0:
        length = min(len(data), random.randint(lmin, lmax))
        info.append(data[0:length])
        data = data[length:]
    return info


def handle_message(message):
    """根据消息类型解析传入的消息。"""
    type = int(message[0:Type_Bytes])
    if type == 1:
        N = int(message[Type_Bytes:Type_Bytes + N_Bytes])
        return type, N
    elif type == 2:
        return type, ""
    elif type == 3:
        length = int(message[Type_Bytes:Type_Bytes+Length_Bytes])
        data = message[Type_Bytes+Length_Bytes:Type_Bytes+Length_Bytes+length]
        return type, length, data
    elif type == 4:
        length = int(message[Type_Bytes:Type_Bytes + Length_Bytes])
        rever_data = message[Type_Bytes + Length_Bytes:Type_Bytes + Length_Bytes + length]
        return type, length, rever_data


def main(server_ip, server_port, lmin, lmax):
    """主函数用于管理客户端与服务器的通信。"""
    data = get_file_message(FILE_IN)
    info = get_send_message(data, lmin, lmax)
    request = "01" + str(len(info)).zfill(Length_Bytes)
    
    client_socket = create_socket()
    client_socket.connect((server_ip, server_port))
    client_socket.send(request.encode())
    
    response = client_socket.recv(Buffer_Size)
    details = handle_message(response.decode())

    if details[0] == 2:
        reverse_info = []
        idx = 1
        for i in info:
            request = "03" + str(len(i)).zfill(Length_Bytes) + i
            client_socket.send(request.encode())
            response = client_socket.recv(Buffer_Size)
            details = handle_message(response.decode())
            if details[0] == 4:
                reverse_info.append(details[2])
                print(f"第{idx}块 : 反转的文本为 {details[2]}")
                idx += 1
            else:
                print('Fetch invalid message')
                return
    else:
        print('Fetch invalid message')
        return

    update_file_message(FILE_OUT, reverse_info)




if __name__ == "__main__":
    # 检查命令行参数的数量是否为5（脚本名称、服务器IP地址、服务器端口号）
    if len(sys.argv) != 5:
        print("Usage: python client.py <server_ip> <server_port> <Lmin> <Lmax>")
        sys.exit(1)

    server_ip = sys.argv[1]  # 获取服务器IP地址
    server_port = sys.argv[2]  # 获取服务器端口号
    lmin = sys.argv[3]     # 获取最小长度
    lmax = sys.argv[4]     # 获取最大长度
    # 检查IP地址是否合法
    if not is_valid_ip(server_ip):
        print("Invalid IP address")
        sys.exit()

    # 检查端口号是否合法
    if not is_valid_port(server_port):
        print("Invalid port")
        sys.exit()

    # 检查输入范围是否合法
    if not is_valid_range(lmin, lmax):
        print("Invalid range")
        sys.exit()

    server_port = int(server_port)  # 将端口号转换为整数
    lmin = int(lmin)  # 将左端点转换为整数
    lmax = int(lmax)  # 将右端点转换为整数

    main(server_ip, server_port, lmin, lmax)
