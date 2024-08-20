#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse
import tzcp.tbk.tbk_pb2 as tbkpb

import etcd3

class DEFS:
    PREFIX = '/tbk/ps'

def __client():
    pkipath = os.path.join(os.path.expanduser("~"),'.tbk/etcdadm/pki')
    return etcd3.client(
        host='127.0.0.1',
        port=2379,
        ca_cert=os.path.join(pkipath,'ca.crt'),
        cert_key=os.path.join(pkipath,'etcdctl-etcd-client.key'),
        cert_cert=os.path.join(pkipath,'etcdctl-etcd-client.crt')
    )

def api_list(args):
    etcd = __client()
    res = etcd.get_prefix(DEFS.PREFIX)
    processes = {}
    publishers = {}
    subscribers = {}

    for r in res:
        key,value = r[1].key.decode(),r[0]
        keys = key[len(DEFS.PREFIX):].split('/')[1:]
        info = None
        if len(keys) == 1:
            info = tbkpb.State()
            info.ParseFromString(value)
            processes[info.uuid] = info
        elif len(keys) == 3:
            if keys[1] == "pubs":
                info = tbkpb.Publisher()
                info.ParseFromString(value)
                publishers[info.uuid] = info
            elif keys[1] == "subs":
                info = tbkpb.Subscriber()
                info.ParseFromString(value)
                subscribers[info.uuid] = info
        else:
            print("Error: key error:",key)
    
    return True, {
        "ps" : processes,
        "pubs" : publishers,
        "subs" : subscribers
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog=f'{os.path.basename(__file__)}',
                        description='console tool for tbk node',
                        epilog='Enjoy the program! :)')
    commands = parser.add_subparsers(dest='command', help='action')
    list = commands.add_parser('list', help='list all nodes & publishers & subscribers')
    help = commands.add_parser('help', help='show help')

    args = parser.parse_args()
    api_table = {
        "list": api_list,
    }
    if args.command in api_table:
        res,info = api_table[args.command](args)
        print(info) if res else print("res : ",res)
    elif args.command == 'help':
        parser.print_help()
    else:
        print("Error: unknown command.")