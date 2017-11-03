
import urllib

DEBUG=True

def save_url_to_file(url, path):
    req = urllib.request.Request(url, headers={'User-Agent':'blah'})
    with urllib.request.urlopen(req) as u:
        with open(path,'wb') as f:
            f.write(u.read())
        if DEBUG: print("save_url_to_file",path)

