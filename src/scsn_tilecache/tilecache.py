import cherrypy
from cherrypy.lib import static
import io
import pathlib
import requests
import magic

class TileCacheWebService(object):

    def __init__(self, conf={}):
        self.conf = self.configure_defaults(conf)
        self.tilecache = TileCache(self.conf['tilecache']['cachedir'])

    def _cp_dispatch(self, vpath):
        print(f"_cp_dispatch: {len(vpath)}")
        if len(vpath) == 1:
            cherrypy.request.params['mapname'] = vpath.pop()
            return self

        if len(vpath) == 4:
            print(f"dispatch for 4")
            cherrypy.request.params['mapname'] = vpath.pop(0)
            cherrypy.request.params['zoom'] = vpath.pop(0)
            cherrypy.request.params['xtile'] = vpath.pop(0)
            cherrypy.request.params['ytile'] = vpath.pop(0)
            return self.tilecache

        return vpath

    @cherrypy.expose
    def index(self, mapname):
        return 'About %s...' % mapname


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
    def __init__(self, cachedir):
        self.cachedir = cachedir
    def loadTile(self, baseUrl, mapname, zoom, xtile, ytile):
        print(f"### Load Remote: {mapname} {zoom}/{xtile}/{ytile}")
        r = requests.get(f'{baseUrl}/{zoom}/{xtile}/{ytile}')
        f = pathlib.Path(f"./{self.cachedir}/{mapname}/{zoom}/{xtile}/{ytile}")
        if r.status_code == requests.codes.ok:
            f.parent.mkdir(parents=True, exist_ok=True)
            tileBytes = r.content
            print(f"bytes in tile: {len(tileBytes)}")
            with open(f, "wb") as cachefile:
                cachefile.write(tileBytes)
            cherrypy.response.headers['Content-Type'] = r.headers['Content-Type']
            return tileBytes
    def getBaseUrl(self, mapname):
        if mapname in self.nameToUrl:
            return self
    @cherrypy.expose
    def index(self, mapname, zoom, xtile, ytile):
        print(f"tilecache: {mapname}")
        f = pathlib.Path(f"./{self.cachedir}/{mapname}/{zoom}/{xtile}/{ytile}")
        if f.exists():
            print(f"serve existing file: {f}")
            filename = f"{f.absolute()}"
            mime = magic.from_file(filename, mime=True)
            return static.serve_file(filename, mime)
        elif mapname == "USGSTopo":
            baseurl= f'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{zoom}/{xtile}/{ytile}'
            return self.loadTile(baseurl, mapname, zoom, xtile, ytile)
        else:
            return f"""
    <html>
    <body>
    <p>Need to get {mapname}/{zoom}/{xtile}/{ytile}</p>
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