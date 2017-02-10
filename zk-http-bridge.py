import os
import urlparse

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError

from bottle import SimpleTemplate, abort, route, run

DEFAULT_HOSTS = os.environ.get("ZK_HOST", "localhost:2181")


def ZK(hosts, path):
    if path.startswith("zk://"):
        path = urlparse.urlparse(path)
        hosts = path.netloc
        path = path.path
    zk = KazooClient(hosts=hosts)
    zk.start()
    return zk, path

index_tpl = SimpleTemplate("""
<html>
<head>
  <title>{{path}}</title>
  <meta charset="utf-8">
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
</head>
<body>
<div class="container">
<div class="row">
<h4>Index for {{path}} </h4>
<ul class="list-unstyled">
% for item in children:
     <li><a href="{{curpath}}{{item}}">{{item}}</a></li>
% end
</ul>
</div>
</div>
</body>
</html>
""")


@route('/<path:path>')
def index(path):
    zk, path = ZK(DEFAULT_HOSTS, path)
    try:
        data, children = zk.retry(zk.get, path)
        if len(data):
            return data
        else:
            children = zk.get_children(path)
            if path.endswith('/'):
                curpath = "./"
            else:
                curpath = os.path.basename(path) + "/"
            return index_tpl.render(path=path, curpath=curpath, children=children)
    except NoNodeError:
        abort(404, "No such node.")

run(server='gunicorn', host='0.0.0.0', port=8080)
