import os
import json
import urllib.parse as urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import admin
import student

class Max_GPA_Server(BaseHTTPRequestHandler):
    
    def parse(self):
        """Helper to extract route and query strings cleanly."""
        parsed_url = urlparse.urlparse(self.path)
        route = parsed_url.path
        query = urlparse.parse_qs(parsed_url.query)
        # Convert list query arguments to single strings
        params = {k: v[0] for k, v in query.items()}
        return route, params

    def _json_helper(self, data, status=200):
        """Transforms data payloads to valid JSON HTTP responses."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
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
                report = student.generate_student_report(major, start, end)
                self._json_helper(report)

        # ADMIN PREVIEW ROUTE
        elif route == "/api/admin/preview-history":
            target_path = os.path.join(os.path.dirname(__file__), '../csv_files/Grade_History.CSV')
            preview = admin.read_grade_history(target_path)
            self._json_helper(preview)
            
        elif route == "/api/admin/preview-degree":
            major_file = params.get("file") # e.g. "Business_Administration_BA.CSV"
            if not major_file:
                self._json_helper({"error": "Missing file parameter"}, 400)
                return
            target_path = os.path.join(os.path.dirname(__file__), f'../csv_files/{major_file}')
            preview = admin.preview_degree_plan(target_path)
            self._json_helper(preview)

        else:
            self._json_helper({"error": "Not Found"}, 404)

    def do_POST(self):
        route, _ = self.parse()

        # ADMIN LOAD ACTIONS
        if route == "/api/admin/load-history":
            target_path = os.path.join(os.path.dirname(__file__), '../csv_files/Grade_History.CSV')
            result = admin.load_grade_history(target_path)
            self._json_helper(result)

        elif route == "/api/admin/load-degree":
            targets = ["Business_Administration_BA.CSV", "Computer_Science_BA.CSV", "Philosophy_BA.CSV"]
            results = {}
            base_dir = os.path.join(os.path.dirname(__file__), '../csv_files/')
            
            for file_name in targets:
                path = os.path.join(base_dir, file_name)
                results[file_name] = admin.load_degree_plan(path)
            self._json_helper({"status": "Success", "details": results})

        elif route == "/api/admin/load-reconciliation":
            target_path = os.path.join(os.path.dirname(__file__), '../csv_files/Reconciliation.CSV')
            recon_map = admin.load_reconciliation(target_path)
            self._json_helper({"status": "Reconciled successfully", "mappings_count": len(recon_map)})

        else:
            self._json_helper({"error": "Not Found"}, 404)

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, Max_GPA_Server)
    print(f"MaxGPA Engine Running locally on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down engine portal.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
