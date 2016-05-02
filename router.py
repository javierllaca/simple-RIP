import select
import socket
from sys import argv
from threading import Thread
import time

BUFFER_SIZE = 1024
UPDATE_INTERVAL = 5.0
ROUTING_TABLE_FMT = '{:<20}{:<20}{:<20}{:<20}'


def parse_link_tuple(link):
    host, port, distance = link.split(':')
    return (socket.gethostbyname(host), int(port)), int(distance)


def timestamp():
    return time.strftime('%H:%M:%S')


class Node:

    def __init__(self, distance, interface=None):
        self.distance = distance
        self.distance_vector = {}
        self.interface = interface


class Router:

    def __init__(self, listening_port, links):
        self.recv_addr = socket.gethostbyname(socket.gethostname()), listening_port
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(self.recv_addr)

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.nodes = {}
        self.neighbors = []

        interface = 1
        for addr, distance in links:
            self.nodes[addr] = Node(distance, interface)
            self.neighbors.append(addr)
            interface += 1

    def run(self):
        self.print_routing_table()
        updater_thread = Thread(target=self.update_neighbors)
        updater_thread.daemon = True
        updater_thread.start()
        while True:
            readables, _, _ = select.select([self.recv_sock] ,[], [], 0)
            for readable in readables:
                if readable == self.recv_sock:
                    packet = self.recv_sock.recv(BUFFER_SIZE)
                    self.process_update(packet)

    def update_neighbors(self):
        while True:
            for addr in self.neighbors:
                self.send_sock.sendto('{}:{}:0,{}'.format(
                    self.ip,
                    self.port,
                    self.distance_vector_string
                ), addr)
            time.sleep(UPDATE_INTERVAL)

    def process_distance_vector(self, distance_vector):
        (neighbor_addr, _), links = distance_vector[0], distance_vector[1:]
        neighbor = self.nodes[neighbor_addr]
        for addr, distance in links:
            neighbor.distance_vector[addr] = distance
            if addr != self.recv_addr and addr not in self.nodes:
                self.nodes[addr] = Node(float('inf'))
        return neighbor

    def process_update(self, packet):
        distance_vector = map(parse_link_tuple, packet.split(','))
        neighbor = self.process_distance_vector(distance_vector)
        changed = False
        for addr, node in self.nodes.items():
            if addr in neighbor.distance_vector:
                if neighbor.distance + neighbor.distance_vector[addr] < node.distance:
                    node.distance = neighbor.distance + neighbor.distance_vector[addr]
                    node.interface = neighbor.interface
                    changed = True
        if changed:
            self.print_routing_table()

    def print_routing_table(self):
        print 'Node {}:{} @ {}'.format(self.ip, self.port, timestamp())
        print ROUTING_TABLE_FMT.format('host', 'port', 'distance', 'interface')
        for (ip, port), node in self.nodes.items():
            print ROUTING_TABLE_FMT.format(ip, port, node.distance, node.interface)

    @property
    def ip(self):
        return self.recv_addr[0]

    @property
    def port(self):
        return self.recv_addr[1]

    @property
    def distance_vector_string(self):
        return ','.join([
            '{}:{}:{}'.format(ip, port, node.distance)
            for (ip, port), node in self.nodes.items()
        ])


if __name__ == '__main__':
    if len(argv) >= 3:
        port = int(argv[1])
        links = map(parse_link_tuple, argv[2:])
        router = Router(port, links)
        router.run()
    else:
        print 'Usage: python <port> <link tuple> ... <link tuple>'
