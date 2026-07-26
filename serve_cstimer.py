import http.server, socketserver, os, ssl, re

VERSION = "2026.06.25"
NOOP_SW = b"""self.addEventListener('install', function(e) { self.skipWaiting(); });
self.addEventListener('activate', function(e) {
  self.registration.unregister().then(function() { return self.clients.claim(); });
});
"""

def get_timer_src_files():
    files = []
    in_timer_src = False
    with open('Makefile') as f:
        for line in f:
            s = line.rstrip('\n').rstrip('\r')
            if s.startswith('timerSrc = '):
                in_timer_src = True
                rest = s.split('timerSrc = $(addprefix $(src)/js/,', 1)[1]
                rest = rest.replace('\\', '').strip()
                if rest:
                    if rest.endswith(')'):
                        rest = rest[:-1].strip()
                        files.append(rest)
                        break
                    files.append(rest)
                continue
            if in_timer_src:
                file_part = s.replace('\\', '').strip()
                if file_part.endswith(')'):
                    file_part = file_part[:-1].strip()
                    if file_part:
                        files.append(file_part)
                    break
                if file_part:
                    files.append(file_part)
    return files

def build_timer_html(compiled=True):
    base = open('dist/timer.php', 'r', encoding='utf-8').read()
    base = base.replace('<html manifest="cache.manifest">', '<html>')
    base = base.replace('<link rel="manifest" href="cstimer.webmanifest">', '')
    meta_title = '''<meta name="keywords" content="计时器, cstimer, 魔方计时器, 在线计时器, 网页计时器">
  <title> csTimer - 魔方竞速训练专用计时器 </title>
  <script type="text/javascript">
    var CSTIMER_VERSION = '%s';
    var LANG_SET = '|en-us|ar-sa|bn-bd|ca-es|cs-cz|da-dk|de-de|el-gr|es-es|fa-ir|fi-fi|fr-fr|he-il|hi-in|hr-hr|hu-hu|it-it|ja-jp|ko-kr|lv-lv|nl-nl|no-no|pl-pl|pt-pt|ro-ro|ru-ru|sk-sk|sl-si|sr-sp|sv-se|tr-tr|uk-ua|vi-vn|zh-cn|zh-tw';
    var LANG_STR = 'English|العربية|বাংলা|Català|Čeština|Dansk|Deutsch|Ελληνικά|Español|فارسی|Suomi|Français|עברית|हिन्दी|Hrvatski|Magyar|Italiano|日本語|한국어|Latviešu|Nederlands|Norsk|Polski|Português|Română|Pусский|Slovenčina|Slovenski|Српски|Svenska|Türkçe|Українська|Tiếng Việt|简体中文|繁體中文';
    var LANG_CUR = 'zh-cn';
  </script>
  <script type="text/javascript" src="/lang/zh-cn.js"></script>''' % VERSION
    base = re.sub(r'<\?php\s+include\([\'"]lang/langDet\.php[\'"]\);\?>', meta_title, base)
    lang_html = open('src/lang/zh-cn.php', 'r', encoding='utf-8').read()
    lang_php = open('src/lang/lang.php', 'r', encoding='utf-8').read()
    lang_html = re.sub(r'<\?php\s+include\([\'"]lang\.php[\'"]\)\s*\?>', lang_php, lang_html)
    lang_html = lang_html.replace('<?php echo $version;?>', VERSION)
    base = re.sub(r'<\?php\s+include\([\'"]lang/[\'"]\.\$lang\.[\'"]\.php[\'"]\)\s*\?>', lang_html, base)
    base = re.sub(r'<\?php\s+include\([\'"]color\.php[\'"]\)\s*\?>', '', base)
    base = re.sub(r'<\?php\s+include\([\'"]baidutongji\.php[\'"]\)\s*\?>', '', base)
    if not compiled:
        script_tags = '\n'.join(['  <script type="text/javascript" src="/src/js/' + f + '"></script>' for f in get_timer_src_files()])
        base = re.sub(r'<script type="text/javascript" src="js/cstimer\.js"></script>', script_tags, base)
        base = re.sub(r'<script type="text/javascript" src="js/twisty\.js"></script>\n?', '', base)
    else:
        base = base.replace('src="js/cstimer.js"', 'src="js/cstimer.js?v=8"')
        base = base.replace('src="js/twisty.js"', 'src="js/twisty.js?v=8"')
    return base

TIMER_HTML_COMPILED = build_timer_html(compiled=True)
TIMER_HTML_SRC = build_timer_html(compiled=False)

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        if path.endswith('.php') or path.endswith('.html'):
            return 'text/html'
        return super().guess_type(path)

    def do_GET(self):
        if self.path in ('/', '/timer.php', '/index.html', '/app.html') or self.path.startswith('/timer.php?') or self.path.startswith('/app.html?'):
            body = TIMER_HTML_COMPILED.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/src.html' or self.path.startswith('/src.html?'):
            body = TIMER_HTML_SRC.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/sw.js':
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Content-Length', str(len(NOOP_SW)))
            self.end_headers()
            self.wfile.write(NOOP_SW)
            return
        if self.path.startswith('/src/js/'):
            rel_path = self.path[len('/src/js/'):]
            file_path = os.path.join('..', 'src', 'js', rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
        if self.path.startswith('/lang/'):
            rel_path = self.path[len('/lang/'):]
            file_path = os.path.join('..', 'src', 'lang', rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
        return super().do_GET()

os.chdir('dist')
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(r'..\cert.pem', r'..\key.pem')
with socketserver.TCPServer(('0.0.0.0', 8443), Handler) as httpd:
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print('Serving dist at https://0.0.0.0:8443')
    httpd.serve_forever()
