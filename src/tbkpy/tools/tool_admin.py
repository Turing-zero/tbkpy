#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse
import subprocess

def api_init(args):
    service_file = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../systemd_file/tbkadmin.service"))
    home_dir = os.path.expanduser("~")
    target_path = os.path.normpath(os.path.join(home_dir,".config/systemd/user"))
    target_file = os.path.join(target_path,"tbkadmin.service")
    os.makedirs(target_path,exist_ok=True)
    # remove if exist
    if os.path.islink(target_file) or os.path.isfile(target_file):
        os.remove(target_file)
    
    os.symlink(service_file,os.path.join(target_path,"tbkadmin.service"))

def api_start(args):
    api_init(args)
    subprocess.run(["systemctl","--user","start","tbkadmin.service"])

def api_stop(args):
    subprocess.run(["systemctl","--user","stop","tbkadmin.service"])

def api_restart(args):
    subprocess.run(["systemctl","--user","restart","tbkadmin.service"])

def api_status(args):
    subprocess.run(["systemctl","--user","status","tbkadmin.service"])

def main():
    parser = argparse.ArgumentParser(
                        prog=f'{os.path.basename(__file__)}',
                        description='console tool for tbk admin',
                        epilog='Enjoy the program! :)')
    command = parser.add_subparsers(dest='command', help='action')
    parser_init = command.add_parser('init', help='init tbk admin service')
    parser_init.set_defaults(func=api_init)
    parser_start = command.add_parser('start', help='start tbk admin service')
    parser_start.set_defaults(func=api_start)
    parser_stop = command.add_parser('stop', help='stop tbk admin service')
    parser_stop.set_defaults(func=api_stop)
    parser_restart = command.add_parser('restart', help='restart tbk admin service')
    parser_restart.set_defaults(func=api_restart)
    parser_status = command.add_parser('status', help='show tbk admin service status')
    parser_status.set_defaults(func=api_status)

    args = parser.parse_args()
    if args.command == 'help' or args.command is None:
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()