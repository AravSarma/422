import os
import sys
import json
import mimetypes
import traceback
import urllib.parse as urlparse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'database'))

import admin
import student
from db_setup import initialize_database

CSV_DIR = os.path.realpath(os.path.join(HERE, '..', 'csv_files'))
# The React frontend is built once (npm run build) and shipped pre-built, so the
# person running the system needs only Python, not Node.
STATIC_DIR = os.path.realpath(os.path.join(HERE, '..', '..', 'frontend', 'dist'))

GRADE_HISTORY_FILE = 'Grade_History.CSV'
RECONCILIATION_FILE = 'Reconciliation.CSV'

# One CSV per degree plan (spec 2.2.2). The major's name is taken from the file
# name: Computer_Science_BA.CSV -> "Computer Science".
DEGREE_PLAN_FILES = {
    "Business_Administration_BA.CSV": "Business Administration",
    "Computer_Science_BA.CSV": "Computer Science",
    "Philosophy_BA.CSV": "Philosophy",
}


def csv_path(file_name):
    """Absolute path of a file inside csv_files/. Only bare file names that exist
    in that folder are accepted, so a request cannot read anywhere else."""
    if os.path.basename(file_name) != file_name:
        raise ValueError("Invalid file name.")
    path = os.path.join(CSV_DIR, file_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{file_name} was not found in backend/csv_files/.")
    return path


class Max_GPA_Server(BaseHTTPRequestHandler):

    def parse(self):
        """Helper to extract route and query strings cleanly."""
        parsed_url = urlparse.urlparse(self.path)
        route = parsed_url.path
        query = urlparse.parse_qs(parsed_url.query)
        params = {k: v[0] for k, v in query.items()}
        return route, params

    def _json_helper(self, data, status=200):
        """Transforms data payloads to valid JSON HTTP responses."""
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, route):
        """Serves the built frontend; unknown paths fall back to index.html."""
        if not os.path.isdir(STATIC_DIR):
            self._json_helper({"error": "The frontend has not been built (frontend/dist is missing). "
                                        "See README.txt."}, 404)
            return
        relative = urlparse.unquote(route).lstrip('/') or 'index.html'
        path = os.path.realpath(os.path.join(STATIC_DIR, relative))
        if not path.startswith(STATIC_DIR + os.sep) or not os.path.isfile(path):
            path = os.path.join(STATIC_DIR, 'index.html')
        with open(path, 'rb') as f:
            body = f.read()
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guarded(self, handler):
        """A handler that raises must still answer, or the browser sees a dead socket."""
        try:
            handler()
        except Exception as e:
            traceback.print_exc()
            self._json_helper({"error": f"{type(e).__name__}: {e}"}, 500)

    def do_GET(self):
        self._guarded(self._get)

    def do_POST(self):
        self._guarded(self._post)

    def _get(self):
        route, params = self.parse()

        # STUDENT API ROUTES
        if route == "/api/majors":
            self._json_helper(student.get_majors())

        elif route == "/api/years":
            self._json_helper(student.get_academic_years())

        elif route == "/api/report":
            major = params.get("major")
            start = params.get("start")
            end = params.get("end")
            if not major or not start or not end:
                self._json_helper({"error": "Missing parameters"}, 400)
            else:
                self._json_helper(student.generate_student_report(major, start, end))

        # ADMIN PREVIEW ROUTES
        elif route == "/api/admin/preview-history":
            self._json_helper(admin.read_grade_history(csv_path(GRADE_HISTORY_FILE)))

        elif route == "/api/admin/preview-degree":
            major_file = params.get("file")  # e.g. "Business_Administration_BA.CSV"
            if major_file not in DEGREE_PLAN_FILES:
                self._json_helper({"error": "Missing or unknown file parameter"}, 400)
                return
            self._json_helper(admin.preview_degree_plan(csv_path(major_file)))

        elif route.startswith("/api/"):
            self._json_helper({"error": "Not Found"}, 404)

        else:
            self._serve_static(route)

    def _post(self):
        route, params = self.parse()

        # ADMIN LOAD ACTIONS - each data set is updated independently (spec 2.2.4)
        if route == "/api/admin/load-history":
            self._json_helper(admin.load_grade_history(csv_path(GRADE_HISTORY_FILE)))

        elif route == "/api/admin/load-degree":
            # ?file=X loads just that plan; with no parameter, all of them.
            wanted = params.get("file")
            if wanted and wanted not in DEGREE_PLAN_FILES:
                self._json_helper({"error": "Unknown file parameter"}, 400)
                return
            results = {}
            for file_name, major_name in DEGREE_PLAN_FILES.items():
                if wanted and file_name != wanted:
                    continue
                results[file_name] = admin.load_degree_plan(csv_path(file_name), major_name)
            self._json_helper({"status": "Success", "details": results})

        elif route == "/api/admin/load-reconciliation":
            recon_map = admin.load_reconciliation(csv_path(RECONCILIATION_FILE))
            self._json_helper({"status": "Reconciled successfully",
                               "mappings_count": recon_map.get("reconciliations_loaded", 0)})

        else:
            self._json_helper({"error": "Not Found"}, 404)

    def log_message(self, format, *args):
        # Keep the terminal readable: only log API calls and errors.
        if '/api/' in (args[0] if args else '') or (len(args) > 1 and str(args[1])[0] in '45'):
            super().log_message(format, *args)


def run_server(port=8000):
    initialize_database(quiet=True)  # creates database.db and its tables if missing
    server_address = ('127.0.0.1', port)  # this machine only; no external access
    httpd = ThreadingHTTPServer(server_address, Max_GPA_Server)
    print(f"MaxGPA is running. Open http://127.0.0.1:{port} in a browser. Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.server_close()


if __name__ == '__main__':
    run_server(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
