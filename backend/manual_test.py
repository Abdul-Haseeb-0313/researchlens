import requests
import os

BASE_URL = "http://localhost:8000"

# ============================================================
# CONFIGURATION – CHANGE THESE AS NEEDED
# ============================================================
USERNAME = "demo_user"
EMAIL = "demo@example.com"
PASSWORD = "demo123"

WORKSPACE_NAME = "My Documents"

# List of PDF file paths you want to upload
PDF_FILES = [
    "/home/user/Downloads/Abdul_Haseeb_Teaching_Resume.pdf",
    "/home/user/Downloads/Epam_Systems_JDN_22-08-2026.pdf",
]

QUESTION = "is he even literate? and is he fit for this job? "
# ============================================================

def register(username, email, password):
    resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    if resp.status_code in (200, 400):  # 400 means already exists
        return resp.json().get("access_token")
    else:
        raise Exception(f"Registration failed: {resp.text}")

def login(username, password):
    resp = requests.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": password
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    else:
        raise Exception(f"Login failed: {resp.text}")

def create_workspace(token, name):
    resp = requests.post(f"{BASE_URL}/workspaces", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={"name": name})
    if resp.status_code == 201:
        return resp.json()["workspace_id"]
    else:
        raise Exception(f"Workspace creation failed: {resp.text}")

def upload_pdfs(token, workspace_id, pdf_paths):
    files = []
    for path in pdf_paths:
        if os.path.exists(path):
            files.append(("files", (os.path.basename(path), open(path, "rb"), "application/pdf")))
        else:
            print(f"⚠️  File not found: {path}")
    if not files:
        raise Exception("No valid PDF files to upload")
    resp = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/upload",
                         headers={"Authorization": f"Bearer {token}"},
                         files=files)
    for _, (_, f, _) in files:
        f.close()
    if resp.status_code == 200:
        print(f"✅ Upload successful: {resp.json()['message']}")
    else:
        raise Exception(f"Upload failed: {resp.text}")

def ask_question(token, workspace_id, question):
    resp = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/ask",
                         headers={"Authorization": f"Bearer {token}",
                                  "Content-Type": "application/json"},
                         json={"question": question})
    if resp.status_code == 200:
        data = resp.json()
        print("\n" + "="*60)
        print("ANSWER")
        print("="*60)
        print(data["answer"])
        print("\n" + "="*60)
        print("CITED SOURCES")
        print("="*60)
        for i, src in enumerate(data["cited_sources"], 1):
            print(f"[{i}] Document: {src.get('document_id')}, Pages: {src.get('page_start')}-{src.get('page_end')}")
            print(f"    Preview: {src.get('text', '')[:200]}...")
        print()
    else:
        raise Exception(f"Question failed: {resp.text}")

if __name__ == "__main__":
    # 1. Try to register, if fails, login
    try:
        token = register(USERNAME, EMAIL, PASSWORD)
        if not token:
            token = login(USERNAME, PASSWORD)
        print(f"🔐 Logged in as {USERNAME}")
    except Exception as e:
        print(e)
        exit(1)

    # 2. Create a workspace
    workspace_id = create_workspace(token, WORKSPACE_NAME)
    print(f"📁 Workspace created: {workspace_id}")

    # 3. Upload PDFs
    upload_pdfs(token, workspace_id, PDF_FILES)

    # 4. Ask a question
    ask_question(token, workspace_id, QUESTION)