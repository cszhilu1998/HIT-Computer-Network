import sys
import json
import socket
import select
import _thread
from urllib.parse import urlparse
import time
import requests

'''代理服务器核心功能'''
class Proxy(object):

    def __init__(self, web_proxy_socket, modified_time, cached_data):
        """
        初始化
        :param web_proxy_socket: 用于侦听客户端的代理服务器套接字实例
        :param modified_time: 修改内容的最新时间(set)
        :param cached_data: 访问数据集(set)
        """
        self.webclient_proxy_socket, (self.webclient_ip, self.webclient_port) = web_proxy_socket.accept()
        # 接受来自WebClient的请求并返回一个新套接字,通过这个新套接字（webclient_proxy_socket）发送和修改消息
        self.BUF_SIZE = 66500  # recv Maximum receive
        self.HTTP_METHOD = ['GET', 'POST'] # HTTP 方法
        self.request = ''
        self.method = ''
        self.port = 80 # 远程服务器端口
        self.host = ''
        self.url = ''
        self.modified_time = modified_time
        self.cached_data = cached_data

    def run(self):
        self.request = self.webclient_proxy_socket.recv(self.BUF_SIZE)
        # 从客户端中得到原始数据，接收TCP数据，数据以字符串形式返回，bufsize指定要接收的最大数据量。
        if not self.request: # 为空时返回
            return
        #print(self.request.decode('utf8','ignore'))
        #print('\n')

        # 分析http消息
        lines = self.request.split(b'\r\n')
        firstline = lines[0].split()
        self.method = firstline[0] # get或post
        self.url = firstline[1]
        parse_url = urlparse(self.url)
        # 将url分解成部件的6元组：<schema>://<net_loc>/<path>;<params>?<query>#<fragment>
        # 例如(scheme='http',netloc='www.hit.edu.cn',path='224/list.psp', params='', query='', fragment='')
        self.host = parse_url.netloc

        '''主模块'''
        if not self.website_filtering(): # 如果非禁止网站
            f_data = self.is_Phishing()
            if f_data: # 如果是钓鱼网站
                self.webclient_proxy_socket.send(bytes(f_data, encoding="utf8")) # 发送TCP数据，将string中的数据发送到连接的套接字。
                self.webclient_proxy_socket.close()
                return
            try:
                sock_info = socket.getaddrinfo(self.host, self.port)[0] # 返回五元组(family,socktype,proto,canonname,sockaddr)
            except BaseException as e:
                sys.exit(1)
            else:
                # 为远程目标服务器构建套接字
                try:
                    self.proxy_trgserver_socket = socket.socket(sock_info[0], sock_info[1])
                    self.proxy_trgserver_socket.connect((self.host, self.port)) # 客户端套接字主动初始化TCP服务器连接
                    self.proxy_trgserver_socket.send(self.request) # 发送TCP数据，将string中的数据发送到连接的套接字
                except:
                    sys.exit(1)
                input = [self.proxy_trgserver_socket, self.webclient_proxy_socket]

                self.cached_modified()

                while True:
                    readable, writable, exceptional = select.select(input, [], input, 3) # (inputs,outputs,inputs,timeout)
                    # 开始 select 监听,对input中的服务端server进行监听
                    # select函数阻塞进程，直到inputs中的套接字被触发,readable返回被触发的套接字（服务器套接字）
                    if exceptional:
                        break

                    # discover triked socket to exchange data
                    # 循环判断是否有客户端连接进来,当有客户端连接进来时select将触发
                    for sock in readable:
                        try:
                            data = sock.recv(self.BUF_SIZE) # 接收TCP数据，数据以字符串形式返回，bufsize指定要接收的最大数据量。
                            if data:
                                if sock is self.proxy_trgserver_socket: # 无钓鱼
                                    self.webclient_proxy_socket.send(data) # 发送TCP数据，将string中的数据发送到连接的套接字。
                                if sock is self.webclient_proxy_socket: # 钓鱼
                                    self.proxy_trgserver_socket.send(data) # 发送TCP数据，将string中的数据发送到连接的套接字。
                            else:
                                break
                        except:
                            break
            self.webclient_proxy_socket.close()
            self.proxy_trgserver_socket.close()


    '''缓存修改后的内容'''
    def cached_modified(self):
        #print(self.cached_data)
        if self.url in self.cached_data:
            cached_time = self.modified_time[self.url]
            # 将修改时间转换为格林尼治平时间
            head = { 'If-Modified-Since': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(cached_time)) }
            try:
                r = requests.get(str(self.url, encoding="utf-8"), headers=head)
                if r.status_code == 304:
                    print('Cached Successful!!!\n')
                    self.webclient_proxy_socket.send(self.cached_data[self.url])
                else:
                    data = self.proxy_trgserver_socket.recv(self.BUF_SIZE)
                    self.cached_data[self.url] = data
                    self.modified_time[self.url] = time.time()
                    self.webclient_proxy_socket.send(data)
            except:
                pass
        else:
            try:
                data = self.proxy_trgserver_socket.recv(self.BUF_SIZE)
            except BaseException as e:
                pass
            else:
                self.cached_data[self.url] = data
                self.modified_time[self.url] =  time.time()
                self.webclient_proxy_socket.send(data)
        fw1 = open('catch_modified_time.txt', 'w')
        fw1.write(str(self.modified_time))
        fw1.close()
        fw2 = open('catch_cached_data.txt', 'w')
        fw2.write(str(self.cached_data))
        fw2.close()

    '''网站过滤，返回true or false'''
    def website_filtering(self):
        with open('webrules.json', 'r') as f:
            webrule_json = json.load(f)
            if self.webclient_ip in webrule_json['ip']: # 非法客户端ip
                print('Forbidden client ip!!!\n')
                return True
            for h in webrule_json['host']: # 非法目标服务器
                host_str = str(self.host, encoding="utf-8")
                if host_str.endswith(h):
                    print('Forbidden server host!!!\n')
                    return True
        return False


    '''网站引导（钓鱼），返回文本 or false'''
    def is_Phishing(self):
        with open('webrules.json', 'r') as f:
            webrule_json = json.load(f)
            for phi in webrule_json['phishing']:
                host_str = str(self.host, encoding="utf-8")
                if host_str == phi:
                    print(str('HTTP/1.1 302 Moved Temporarily\r\n'
                        'Location: http://' +webrule_json['phishing'][host_str] + '\r\n\r\n'))
                    return str('HTTP/1.1 302 Moved Temporarily\r\n'
                        'Location: http://' +webrule_json['phishing'][host_str] + '\r\n\r\n')
        return False


'''代理服务器'''
class Proxy_Server(object):
    def __init__(self, ip, port, maxnum):
        '''
        代理服务器初始化
        :param ip: 代理服务器IP地址
        :param port: 代理服务器端口号
        :param Cnum: 代理服务器允许的最多的客户端连接数
        '''

        self.ip = ip
        self.port = port
        self.web_proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建套接字连接客户端 (IPV4, TCP)
        self.web_proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reset socket
        self.web_proxy_socket.bind((ip, port)) # 使用bind函数绑定代理服务器IP 地址，端口号
        self.web_proxy_socket.listen(maxnum)  # 使用listen函数进行监听创建的socket。
        self.modified_time = dict() # 存储修改数据的最后时间
        self.cache_data = dict() # 存储修改过的数据

    def run(self):
        print ("代理服务器正在（ip: %s ，port: %s ）上运行"%(str(self.ip), str(self.port)))
        while True:
            # 多线程
            _thread.start_new_thread(Proxy(self.web_proxy_socket, self.modified_time, self.cache_data).run, ())


if __name__ == '__main__':
    Proxy_Server('127.0.0.1', 10240, 5).run()
