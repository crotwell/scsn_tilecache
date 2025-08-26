import cherrypy
from cherrypy.lib import static
import io
import pathlib
import requests
import magic

class TileCacheWebService(object):

    def __init__(self, conf={}):
        self.conf = self.configure_defaults(conf)
        self.tilecache = TileCache(self.conf['tilecache']['cachedir'],
                                   self.conf['tilecache']['nameToUrl'])

    def _cp_dispatch(self, vpath):
        print(f"_cp_dispatch: {len(vpath)}")
        if len(vpath) == 0:
            return self.knownMaps()

        if len(vpath) == 1:
            cherrypy.request.params['mapname'] = vpath.pop()
            return self

        if len(vpath) == 4:
            print(f"dispatch for 4")
            cherrypy.request.params['mapname'] = vpath.pop(0)
            cherrypy.request.params['zoom'] = vpath.pop(0)
            cherrypy.request.params['ytile'] = vpath.pop(0)
            cherrypy.request.params['xtile'] = vpath.pop(0)
            return self.tilecache

        return vpath

    @cherrypy.expose
    def index(self, mapname=None):
        if mapname is not None:
            return 'About %s...' % mapname
        else:
            return self.knownMaps()
    def knownMaps(self):
        html = f"""<html>
        <body>
        <ul>
        """
        for mapname, baseurl in self.conf['tilecache']['nameToUrl'].items():
            if len(baseurl)>0:
                html += f"<li><a href=\"{mapname}\">{mapname}</a> <a href=\"{baseurl}\">{baseurl}</a></li>\n"
            else:
                html += f"<li><a href=\"{mapname}\">{mapname}</a></li>\n"

        html += "</ul></body></html>"
        return html


    def configure_defaults(self, conf):
        defaults = {
            "dataselect": {
                "maxqueryhours": "24",
            },
            "ringserver": {
                "host": "127.0.0.1",
                "port": "80",
            }
        }
        out = {}
        out.update(defaults)
        out.update(conf)
        return out

class TileCache(object):
    def __init__(self, cachedir, nameToUrl):
        self.cachedir = pathlib.Path(cachedir)
        self.cachedir.mkdir(parents=True, exist_ok=True)
        self.nameToUrl = nameToUrl
        print(f"Init cachedir: {self.cachedir}")
    def loadTile(self, baseUrl, mapname, zoom, ytile, xtile):
        print(f"### Load Remote: {mapname} {zoom}/{ytile}/{xtile}")
        if '{z}' in baseUrl and '{y}' in baseUrl and '{x}' in baseUrl:
            reqUrl = baseUrl.replace('{z}', zoom).replace('{y}', ytile).replace('{x}', xtile)
        else:
            reqUrl = f'{baseUrl}/{zoom}/{ytile}/{xtile}'
        r = requests.get(reqUrl)
        print(f"   {r.url}")
        f = pathlib.Path(self.cachedir, f"{mapname}/{zoom}/{ytile}/{xtile}")
        if r.status_code == requests.codes.ok:
            f.parent.mkdir(parents=True, exist_ok=True)
            tileBytes = r.content
            with open(f, "wb") as cachefile:
                cachefile.write(tileBytes)
            print(f"wrote {len(tileBytes)} bytes to {f}")
            cherrypy.response.headers['Content-Type'] = r.headers['Content-Type']
            return tileBytes
        else:
            print("response not ok")
            print(r.text)
    def getBaseUrl(self, mapname):
        if mapname in self.nameToUrl:
            return self.nameToUrl['mapname']
    @cherrypy.expose
    def index(self, mapname, zoom, ytile, xtile):
        print(f"tilecache: {mapname}")
        extension = ""
        if xtile.endswith(".png"):
            extension = ".png"
            xtile = xtile[:-4]
        if not (zoom.isdigit() and ytile.isdigit() and xtile.isdigit()):
            raise Exception(f"Unknown params zoom:{zoom}  y:{ytile}  x:{xtile}")
        f = pathlib.Path(self.cachedir, f"{mapname}/{zoom}/{ytile}/{xtile}{extension}")
        cherrypy.response.headers["Cache-Control"] = "max-age=86400"
        if f.exists():
            print(f"serve existing file: {f}")
            filename = f"{f.absolute()}"
            mime = magic.from_file(filename, mime=True)
            return static.serve_file(filename, mime)
        elif mapname in self.nameToUrl:
            baseurl = self.nameToUrl[mapname]
            if len(baseurl) > 0:
                print(f"load from urlmap: {baseurl}")
                return self.loadTile(baseurl, mapname, zoom, ytile, xtile)
        cherrypy.response.headers["Cache-Control"] = "max-age=0"
        return f"""
    <html>
    <body>
    <p>Need to get {mapname}/{zoom}/{ytile}/{xtile}{extension}</p>
    <p>but unknown map name: {mapname}</p>
    </body>
    </html>
    """

if __name__ == 'xxx__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }

    cherrypy.quickstart(TileCacheWebService(), '/', conf)

if __name__ == '__main__':
    cherrypy.quickstart(TileCacheWebService())
