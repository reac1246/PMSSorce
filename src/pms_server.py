import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- Configuration ---
STORAGE_DIR = "storage"
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

# Ensure directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# --- Helpers ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def check_auth(login_id, login_pw):
    users = load_json(USERS_FILE, {"pms_admin": "pms_password"})
    return users.get(login_id) == login_pw

def generate_mgmt_num():
    import random
    rand_prefix = str(random.randint(100, 999))
    rand_suffix = str(random.randint(1000, 9999))
    return f"{rand_prefix}-{rand_suffix}-JMN"

# --- API Endpoints ---

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    if check_auth(data.get("login_id"), data.get("login_pw")):
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route("/info", methods=["GET"])
def info():
    login_id = request.args.get("login_id")
    login_pw = request.args.get("login_pw")
    mgmt_num = request.args.get("management_number")
    
    if not check_auth(login_id, login_pw):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    projects = load_json(PROJECTS_FILE, {})
    if mgmt_num in projects:
        return jsonify(projects[mgmt_num]), 200
    return jsonify({"status": "error", "message": "Project not found"}), 404

@app.route("/setup", methods=["POST"])
def setup():
    login_id = request.form.get("login_id")
    login_pw = request.form.get("login_pw")
    project_name = request.form.get("project_name")
    mgmt_num = request.form.get("management_number")
    
    if not check_auth(login_id, login_pw):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    if not mgmt_num:
        mgmt_num = generate_mgmt_num()
        
    projects = load_json(PROJECTS_FILE, {})
    if mgmt_num in projects:
        # If it already exists, maybe treat as update? But setup usually means fresh.
        pass

    # Save file
    file = request.files.get("file")
    if not file:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    project_dir = os.path.join(STORAGE_DIR, mgmt_num)
    os.makedirs(project_dir, exist_ok=True)
    
    version = "1.0.0"
    filename = f"v{version}.zip"
    file.save(os.path.join(project_dir, filename))
    
    projects[mgmt_num] = {
        "project_name": project_name,
        "management_number": mgmt_num,
        "latest_version": version,
        "versions": [version],
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat(),
        "owner": login_id
    }
    save_json(PROJECTS_FILE, projects)
    
    return jsonify({"status": "ok", "management_number": mgmt_num, "version": version}), 200

@app.route("/push", methods=["POST"])
def push():
    login_id = request.form.get("login_id")
    login_pw = request.form.get("login_pw")
    mgmt_num = request.form.get("management_number")
    
    if not check_auth(login_id, login_pw):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    projects = load_json(PROJECTS_FILE, {})
    if mgmt_num not in projects:
        return jsonify({"status": "error", "message": "Project not found"}), 404
        
    file = request.files.get("file")
    if not file:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    # Increment version
    current_ver = projects[mgmt_num]["latest_version"]
    parts = list(map(int, current_ver.split('.')))
    parts[-1] += 1
    new_ver = ".".join(map(str, parts))
    
    project_dir = os.path.join(STORAGE_DIR, mgmt_num)
    filename = f"v{new_ver}.zip"
    file.save(os.path.join(project_dir, filename))
    
    projects[mgmt_num]["latest_version"] = new_ver
    projects[mgmt_num]["versions"].append(new_ver)
    projects[mgmt_num]["updated_at"] = datetime.datetime.now().isoformat()
    save_json(PROJECTS_FILE, projects)
    
    return jsonify({"status": "ok", "version": new_ver}), 200

@app.route("/versions", methods=["GET"])
def list_versions():
    login_id = request.args.get("login_id")
    login_pw = request.args.get("login_pw")
    mgmt_num = request.args.get("management_number")
    
    if not check_auth(login_id, login_pw):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    projects = load_json(PROJECTS_FILE, {})
    if mgmt_num in projects:
        return jsonify({"versions": projects[mgmt_num]["versions"]}), 200
    return jsonify({"status": "error", "message": "Project not found"}), 404

@app.route("/download", methods=["GET"])
def download():
    login_id = request.args.get("login_id")
    login_pw = request.args.get("login_pw")
    mgmt_num = request.args.get("management_number")
    version = request.args.get("version")
    
    if not check_auth(login_id, login_pw):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    projects = load_json(PROJECTS_FILE, {})
    if mgmt_num not in projects:
        return jsonify({"status": "error", "message": "Project not found"}), 404
        
    if not version or version == "LATEST":
        version = projects[mgmt_num]["latest_version"]
        
    if version not in projects[mgmt_num]["versions"]:
         # Fallback to check if file exists anyway or try to match prefix
         pass

    file_path = os.path.join(STORAGE_DIR, mgmt_num, f"v{version}.zip")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"{projects[mgmt_num]['project_name']}_v{version}.zip")
    
    return jsonify({"status": "error", "message": "Version file not found"}), 404

if __name__ == "__main__":
    import sys
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print(f"PMS Data Center Server starting on port {port}...")
    print(f"Storage: {os.path.abspath(STORAGE_DIR)}")
    app.run(host="0.0.0.0", port=port)
