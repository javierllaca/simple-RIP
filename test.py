import socket
from subprocess import Popen
from sys import argv


def build_network(path, port=2000):
    network = {}
    with open(path, 'r') as network_file:
        for line in network_file:
            u, v, c = line.strip().split(',')
            if u not in network:
                network[u] = port, []
                port += 1
            if v not in network:
                network[v] = port, []
                port += 1
            network[u][1].append((v, c))
            network[v][1].append((u, c))
    return network


def make_commands(network):
    for u, (port, neighbors) in network.items():
        yield 'python router.py {} {} > {}.txt'.format(port, ' '.join([
            '{}:{}:{}'.format(
                socket.gethostbyname(socket.gethostname()),
                network[v][0],
                c
            ) for v, c in neighbors
        ]), port)


if len(argv) == 2:
    network = build_network(argv[1])
    processes = [Popen(cmd, shell=True) for cmd in make_commands(network)]
    for process in processes:
        process.wait()
else:
    print 'usage: python {} <network file>'.format(argv[0])
