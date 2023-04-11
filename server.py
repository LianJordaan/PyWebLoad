import http.server
import socketserver
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin

PORT = 8000

class ProxyRequestHandler(http.server.SimpleHTTPRequestHandler):


    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <div id="site-container"></div>
                <input type="text" id="input-url">
                <button id="load-button">Load</button>
                <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
                <script>
                    $(document).ready(function() {
                        $('#load-button').click(function() {
                            var url = $('#input-url').val();
                            $.ajax({
                                url: "/proxy?url=" + encodeURIComponent(url),
                                success: function(data) {
                                    location.href = "/proxy?url=" + url;
                                }
                            });
                        });
                    });
                </script>
            """)
        elif self.path.startswith("/proxy?url="):
            url = unquote(self.path[len("/proxy?url="):])
            if not url.startswith("http"):
                url = "http://" + url
            resp = requests.get(url)
            self.send_response(resp.status_code)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            content = resp.content
            if resp.encoding != 'utf-8':
                content = content.decode(resp.encoding)
            else:
                content = content.decode('utf-8')
            
            soup = BeautifulSoup(content, 'html.parser')

            for link in soup.find_all('a'):
                href = link.get('href') or link.get('src')
                if href and not href.startswith('http'):
                    link['href'] = link['src'] = "/proxy?url=" + urljoin(url, href)
            
            for link in soup.find_all('link'):
                link_href = link.get('href')
                if link_href:
                    link['href'] = urljoin(url, link_href)
            
            for script in soup.find_all('script'):
                script_src = script.get('src')
                if script_src:
                    script['src'] = urljoin(url, script_src)
            
            for img in soup.find_all('img'):
                img_src = img.get('src')
                if img_src:
                    img['src'] = urljoin(url, img_src)
            
            self.wfile.write(str(soup).encode('utf-8'))
    
        else:
            super().do_GET()



with socketserver.TCPServer(("", PORT), ProxyRequestHandler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
