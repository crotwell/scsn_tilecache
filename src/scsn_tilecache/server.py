import cherrypy
from cherrypy.process.plugins import Daemonizer

import argparse
import datetime
import io
import os
import sys
from .tilecache import TileCacheWebService


# tomllib is std in python > 3.11 so do conditional import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def do_parseargs():
    parser = argparse.ArgumentParser(
        description="Find gaps in miniseed archive and attempt to recover missing data."
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--daemon", help="run as daemon via fork", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--conf",
        required=False,
        help="Configuration as TOML",
        type=argparse.FileType("rb"),
    )
    return parser.parse_args()

def main():

    args = do_parseargs()
    ringconf = tomllib.load(args.conf)
    args.conf.close()
    port = ringconf['tilecache'].get('port', 9090)

    cherrypy.config.update({'server.socket_port': port})
    cherrypy.config.update({'server.socket_host': "0.0.0.0"})
    cherrypy.tree.mount(TileCacheWebService(ringconf),
                        '/tilecache'
                        )
    print()
    print(f"  http://localhost:{port}/tilecache/")
    print()
    if args.daemon:
        d = Daemonizer(cherrypy.engine)
        d.subscribe()
    else:
        cherrypy.engine.start()
        cherrypy.engine.block()

if __name__ == '__main__':
    main()
