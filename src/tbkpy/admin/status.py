import os, sys, time, threading
# add the path of tbkpy to sys.path
sys.path.append("..")
import json
import psutil, socket
from tbkpy.socket import UDPMultiCastReceiver, UDPMultiCastSender
from tbkpy.config import MULTICAST_GROUP, PORT_TBK_STATUS, TBK_STATUE_INTERVAL, TBK_STATUS_ALIVE_TIMEOUT
import tbkpy.tools.tool_etcd as tbketcd
import tbkpy.tools.tool_etcdadm as tbketcdadm

class Status:
    interfaces = {} # got interface and ip from raw psutil
    ip = "0.0.0.0" # got ip from etcd
    health = "unknown"
    clusters = []
    def __repr__(self):
        return f"Status({self.ip}, {self.health}, {self.clusters}, {self.interfaces})"


class TBKLocal:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.etcdadm_bin = f"{self.home}/.tbk/etcdadm/bin/etcdadm"
        self.etcd_bin = f"{self.home}/.tbk/etcdadm/bin/etcd"
        self.etcdctl_bin = f"{self.home}/.tbk/etcdadm/bin/etcdctl.sh"
    def getEtcdEndpoints(self):
        res, output = tbketcd.api_info("{ENDPOINT}")
        return (res, []) if res != 0 else (res, output.strip().split("\n"))
    def getEtcdHealth(self):
        res, output = tbketcd.api_health("{ENDPOINT},{HEALTH}")
        if res != 0:
            return res, ""
        health = {}
        for info in output.strip().split("\n"):
            if info == "":
                continue
            endpoint, h = info.split(",")
            health[endpoint] = h
        return res, health
    def getEtcdInfo(self):
        res, output = tbketcd.api_ipinfo()
        return (res, json.loads(output)) if res == 0 else (res, {})
    def adminReset(self):
        res, output = tbketcdadm.api_run_action("reset")
    def adminInit(self):
        res, output = tbketcdadm.api_run_action("init")
    def getRawInterfaces(self):
        ifs = {}
        interfaces = psutil.net_if_addrs()
        for if_name, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ifs[if_name] = addr.address
        return ifs

    def getStatus(self):
        status = Status()
        status.interfaces = self.getRawInterfaces()
        res, info = self.getEtcdInfo()
        if res != 0:
            status.health = "unknown"
            return status
        status.ip = info['clientURLs'][0]
        res, health = self.getEtcdHealth()
        if res != 0 or status.ip not in health:
            return status
        status.health = health[status.ip]
        res, endpoints = self.getEtcdEndpoints()
        if res != 0:
            return status
        status.clusters = endpoints
        return status

class StatusNode:
    def __init__(self):
        self.tbklocal = TBKLocal()
        self.receiver = UDPMultiCastReceiver(MULTICAST_GROUP, PORT_TBK_STATUS)
        self.sender = UDPMultiCastSender()
        self.all_info_mutex = threading.Lock()
        self.all_info = {}
        self._threads = (
            threading.Thread(target=self.__send),
            threading.Thread(target=self.__recv)
        )
        self._status = Status()
        for t in self._threads:
            t.daemon = True
            t.start()
    def __send(self):
        while True:
            self._status = self.tbklocal.getStatus()
            for if_name, ip in self._status.interfaces.items():
                if if_name == "lo":
                    continue
                self.sender.setInterface(ip)
                self.sender.send(json.dumps(self._status.__dict__).encode(), (MULTICAST_GROUP, PORT_TBK_STATUS))
            time.sleep(TBK_STATUE_INTERVAL)
            self.all_info_mutex.acquire()
            for endpoint in list(self.all_info.keys()):
                if time.time() - self.all_info[endpoint][1] > TBK_STATUS_ALIVE_TIMEOUT:
                    del self.all_info[endpoint]
            self.all_info_mutex.release()
    def __recv(self):
        while True:
            res, recv = self.receiver.recv()
            # print("recv : ",res, recv)
            if res:
                msg, endpoint = recv
                msg = json.loads(msg.decode())
                if "ip" in msg and msg["ip"] == self._status.ip: # skip the local status
                    continue
                self.all_info_mutex.acquire()
                self.all_info[endpoint[0]] = (msg, time.time())
                self.all_info_mutex.release()
            time.sleep(0.01)
    @property
    def info(self):
        return self.all_info
    @property
    def localStatus(self):
        return self._status

if __name__ == "__main__":
    sn = StatusNode()
    while True:
        print("Got Info : ",sn.info)
        time.sleep(1)