"""
========================================================================================
PRAAPTI AI - Civic Intelligence Local Web & API Server
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
    query_opensearch_schemes
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

                # Route 3: Anti-Scam Phishing Scan
                elif self.path == "/api/fraud-scan":
                    input_text = str(data.get("url_or_text", "")).lower()
                    fraud_file = os.path.join(backend_dir, "data/fraud_patterns.json")
                    
                    suspicious_domains = ["pmkisan-gov.in", "pm-kisan-yojna.org", "ayushmanbharat-card.online", "free-ration-card.info"]
                    if os.path.exists(fraud_file):
                        try:
                            with open(fraud_file, "r", encoding="utf-8") as f:
                                f_data = json.load(f)
                                suspicious_domains = f_data.get("suspicious_domains", suspicious_domains)
                        except Exception:
                            pass

                    flagged = []
                    is_scam = False
                    for sd in suspicious_domains:
                        if sd in input_text:
                            is_scam = True
                            flagged.append(f"Domain matches known scam registry: '{sd}'")

                    if any(kw in input_text for kw in ["upi", "registration fee", "qr code", "instant prize", "advance fee"]):
                        is_scam = True
                        flagged.append("Demands upfront fee or UPI transfer (Government welfare schemes are ALWAYS free to apply)")

                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "is_safe": not is_scam,
                        "risk_level": "HIGH_RISK" if is_scam else "SAFE",
                        "flagged_issues": flagged
                    }).encode('utf-8'))
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
