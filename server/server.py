from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import json
import os

import admin
import student

class Max_GPA_Server(BaseHTTPRequestHandler):

    def parse(self):
        return None

    def _json_helper(self, data, status = 200):
        return None
    

def run_server(port=8000):
    return None


if __name__ == '__main__':
    run_server()