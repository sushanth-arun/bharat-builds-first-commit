"""
========================================================================================
PRAAPTI AI - Civic Intelligence Local Web & API Server
Subsystem: Teammate 2 (Sanjay) - Civic Dashboard UI & Real-Time Visualization Server
Serves the modern accessible civic dashboard on http://localhost:8080 and handles
dynamic agent workflow requests via /api/workflow.
========================================================================================
"""

import http.server
import socketserver
import os
import sys
import json
import logging
from datetime import datetime

# Ensure backend root is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import (
    CitizenProfile,
    RTIApplicationPayload,
    run_praapti_agent_workflow,
    check_cedar_policy,
    generate_statutory_rti_text,
    query_opensearch_schemes,
    process_strands_chatbot_query,
    verify_portal_authenticity_tool
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("praapti.ui_server")

PORT = 8080
TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))

class PraaptiHttpHandler(http.server.SimpleHTTPRequestHandler):
    """
    Combined static file server and dynamic JSON API handler for PRAAPTI AI.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEMPLATES_DIR, **kwargs)

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_POST(self):
        """Handles dynamic agent API requests."""
        if self.path.startswith("/api/"):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_body) if post_body else {}

                # Route 1: Dynamic Agent Workflow
                if self.path == "/api/workflow" or self.path == "/api/schemes/match":
                    logger.info(f"Processing dynamic agent workflow for citizen: {data.get('name', 'Anonymous')}")
                    profile = CitizenProfile(**data)
                    result = run_praapti_agent_workflow(profile)
                    
                    self._set_headers(200)
                    self.wfile.write(result.model_dump_json().encode('utf-8'))
                    return

                # Route 2: RTI Draft Generation
                elif self.path == "/api/rti/generate":
                    payload = RTIApplicationPayload(**data)
                    auth = check_cedar_policy(
                        user_role="Citizen",
                        action=f"Draft{payload.tier.upper()}RTI",
                        resource_tier=payload.tier,
                        is_verified=payload.is_verified,
                        kyc_level=payload.kyc_level
                    )
                    
                    if auth.get("decision") != "ALLOW":
                        self._set_headers(403)
                        self.wfile.write(json.dumps({
                            "status": "DENIED",
                            "reason": auth.get("reason"),
                            "cedar_status": auth
                        }).encode('utf-8'))
                        return

                    draft = generate_statutory_rti_text(payload)
                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "status": "SUCCESS",
                        "tier": payload.tier,
                        "draft_content": draft,
                        "cedar_status": auth
                    }).encode('utf-8'))
                    return

                # Route 3: Anti-Scam Phishing Scan (Strands Agent Tool)
                elif self.path == "/api/fraud-scan":
                    input_text = str(data.get("url_or_text", "")).strip()
                    scan_result = verify_portal_authenticity_tool(input_text)

                    self._set_headers(200)
                    self.wfile.write(json.dumps(scan_result).encode('utf-8'))
                    return

                # Route 4: AI Civic Chat Assistant & Dynamic Doubts Resolver (Strands SDK Agent)
                elif self.path == "/api/chat":
                    user_query = str(data.get("message", "")).strip()
                    context_profile = data.get("profile", {})
                    matched_schemes = data.get("matched_schemes", [])

                    # Call Strands SDK agent with AWS Cedar & OpenSearch tool suite
                    chat_result = process_strands_chatbot_query(
                        user_query=user_query,
                        context_profile=context_profile,
                        matched_schemes=matched_schemes
                    )

                    self._set_headers(200)
                    self.wfile.write(json.dumps(chat_result).encode('utf-8'))
                    return

                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))
                    return

            except Exception as e:
                logger.error(f"API Error: {e}", exc_info=True)
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        # Fallback to default
        super().do_POST()

    def do_GET(self):
        """Serves UI index.html on root or static requests with zero cache."""
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        self.send_response(200)
        if self.path.endswith(".html"):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path.endswith(".css"):
            self.send_header("Content-Type", "text/css; charset=utf-8")
        elif self.path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        elif self.path.endswith(".json"):
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        
        file_path = os.path.join(TEMPLATES_DIR, self.path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        
        return super().do_GET()


if __name__ == "__main__":
    print("=" * 80)
    print("PRAAPTI AI - Civic Intelligence Local Web & Agent Server")
    print("=" * 80)
    print(f"[*] Serving Modern Civic Portal at: http://localhost:{PORT}")
    print(f"[*] Direct Agent API live at:      http://localhost:{PORT}/api/workflow")
    print("Press Ctrl+C to terminate.")
    print("=" * 80)

    # Allow socket address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), PraaptiHttpHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] PRAAPTI Server terminated safely.")
