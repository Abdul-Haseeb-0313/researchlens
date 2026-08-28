import requests
import json
import os

BASE_URL = "http://localhost:8000"

# Sample PDF paths (adjust if needed)
SAMPLE_PDFS = [
    "../documents/sample.pdf",
    "../documents/sample2.pdf",
]

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def register(username, email, password):
    url = f"{BASE_URL}/register"
    payload = {"username": username, "email": email, "password": password}
    resp = requests.post(url, json=payload)
    return resp

def login(username, password):
    url = f"{BASE_URL}/login"
    data = {"username": username, "password": password}
    resp = requests.post(url, data=data)  # OAuth2 form data
    return resp

def create_workspace(token, name):
    url = f"{BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": name}
    resp = requests.post(url, json=payload, headers=headers)
    return resp

def list_workspaces(token):
    url = f"{BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    return resp

def upload_pdf(token, workspace_id, file_paths):
    url = f"{BASE_URL}/workspaces/{workspace_id}/upload"
    headers = {"Authorization": f"Bearer {token}"}
    files = []
    for path in file_paths:
        if os.path.exists(path):
            files.append(("files", (os.path.basename(path), open(path, "rb"), "application/pdf")))
        else:
            print(f"Warning: {path} not found, skipping")
    if not files:
        return None
    resp = requests.post(url, headers=headers, files=files)
    for _, (_, f, _) in files:
        f.close()
    return resp

def ask_question(token, workspace_id, question):
    url = f"{BASE_URL}/workspaces/{workspace_id}/ask"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"question": question}
    resp = requests.post(url, json=payload, headers=headers)
    return resp

def get_me(token):
    url = f"{BASE_URL}/me"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    return resp

def main():
    # ==============================
    # 1. User Registration
    # ==============================
    print_section("1. User Registration")

    # Register user1
    resp = register("alice", "alice@example.com", "password123")
    print("Register Alice:", resp.status_code, resp.json())
    assert resp.status_code == 200, "Alice registration failed"

    # Register user2
    resp = register("bob", "bob@example.com", "password456")
    print("Register Bob:", resp.status_code, resp.json())
    assert resp.status_code == 200, "Bob registration failed"

    # Try duplicate username
    resp = register("alice", "alice2@example.com", "password")
    print("Duplicate username:", resp.status_code, resp.json())
    assert resp.status_code == 400, "Duplicate username should fail"

    # Try duplicate email
    resp = register("alice2", "alice@example.com", "password")
    print("Duplicate email:", resp.status_code, resp.json())
    assert resp.status_code == 400, "Duplicate email should fail"

    # ==============================
    # 2. Login
    # ==============================
    print_section("2. Login")

    # Correct login
    resp = login("alice", "password123")
    print("Alice login:", resp.status_code, resp.json())
    assert resp.status_code == 200, "Alice login failed"
    token_alice = resp.json()["access_token"]

    resp = login("bob", "password456")
    print("Bob login:", resp.status_code, resp.json())
    assert resp.status_code == 200, "Bob login failed"
    token_bob = resp.json()["access_token"]

    # Wrong password
    resp = login("alice", "wrongpass")
    print("Wrong password:", resp.status_code, resp.json())
    assert resp.status_code == 401, "Wrong password should be 401"

    # ==============================
    # 3. Workspace Creation & Listing
    # ==============================
    print_section("3. Workspace Creation & Listing")

    # Alice creates two workspaces
    resp = create_workspace(token_alice, "Alice Research")
    print("Alice create workspace 1:", resp.status_code, resp.json())
    assert resp.status_code == 201
    alice_ws1 = resp.json()["workspace_id"]

    resp = create_workspace(token_alice, "Alice Personal")
    print("Alice create workspace 2:", resp.status_code, resp.json())
    assert resp.status_code == 201
    alice_ws2 = resp.json()["workspace_id"]

    # Bob creates one workspace
    resp = create_workspace(token_bob, "Bob's Docs")
    print("Bob create workspace:", resp.status_code, resp.json())
    assert resp.status_code == 201
    bob_ws = resp.json()["workspace_id"]

    # List workspaces for Alice
    resp = list_workspaces(token_alice)
    print("Alice's workspaces:", resp.status_code, resp.json())
    assert resp.status_code == 200
    alice_workspaces = resp.json()
    assert len(alice_workspaces) == 2

    # List workspaces for Bob
    resp = list_workspaces(token_bob)
    print("Bob's workspaces:", resp.status_code, resp.json())
    assert resp.status_code == 200
    bob_workspaces = resp.json()
    assert len(bob_workspaces) == 1

    # ==============================
    # 4. Upload PDFs
    # ==============================
    print_section("4. Upload PDFs")

    # Upload to Alice's first workspace (two PDFs)
    pdf_files = SAMPLE_PDFS
    resp = upload_pdf(token_alice, alice_ws1, pdf_files)
    print("Alice upload to ws1:", resp.status_code, resp.json() if resp else "No files")
    assert resp is not None and resp.status_code == 200

    # Upload to Alice's second workspace (one PDF)
    resp = upload_pdf(token_alice, alice_ws2, [pdf_files[0]])
    print("Alice upload to ws2:", resp.status_code, resp.json() if resp else "No files")
    assert resp is not None and resp.status_code == 200

    # Upload to Bob's workspace (one PDF)
    resp = upload_pdf(token_bob, bob_ws, [pdf_files[1]])
    print("Bob upload:", resp.status_code, resp.json() if resp else "No files")
    assert resp is not None and resp.status_code == 200

    # Upload invalid file (non-PDF) - should be ignored or error
    # We'll simulate by trying to upload a text file
    with open("test.txt", "w") as f:
        f.write("Not a PDF")
    resp = upload_pdf(token_alice, alice_ws1, ["test.txt"])
    print("Upload non-PDF:", resp.status_code, resp.json() if resp else "No files")
    # It should either return error or process 0 files; we just check it doesn't crash
    # We'll not assert strict here.

    # ==============================
    # 5. Ask Questions
    # ==============================
    print_section("5. Ask Questions")

    # Ask in Alice's ws1 (has two docs)
    question = "What is the main topic of these documents?"
    resp = ask_question(token_alice, alice_ws1, question)
    print("Alice ask ws1:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Answer snippet:", data["answer"][:100])
        print("Cited sources count:", len(data["cited_sources"]))
    else:
        print("Error:", resp.json())

    # Ask in Alice's ws2 (has one doc)
    resp = ask_question(token_alice, alice_ws2, "Summarize the document.")
    print("Alice ask ws2:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Answer snippet:", data["answer"][:100])
    else:
        print("Error:", resp.json())

    # Ask in Bob's workspace
    resp = ask_question(token_bob, bob_ws, "What projects are mentioned?")
    print("Bob ask:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Answer snippet:", data["answer"][:100])

    # Ask in empty workspace (Alice's ws2? Already has doc, so skip; we can test with a new workspace)
    resp = create_workspace(token_alice, "Empty")
    empty_ws = resp.json()["workspace_id"]
    resp = ask_question(token_alice, empty_ws, "Anything?")
    print("Ask in empty workspace:", resp.status_code, resp.json())

    # ==============================
    # 6. Authorization Tests
    # ==============================
    print_section("6. Authorization Tests")

    # Bob tries to access Alice's workspace
    resp = ask_question(token_bob, alice_ws1, "What is the main topic?")
    print("Bob asks in Alice's ws1:", resp.status_code, resp.json())
    assert resp.status_code == 404, "Bob should not access Alice's workspace"

    # Bob tries to upload to Alice's workspace
    resp = upload_pdf(token_bob, alice_ws1, pdf_files[:1])
    print("Bob uploads to Alice's ws1:", resp.status_code, resp.json() if resp else "No files")
    assert resp.status_code == 404

    # Bob tries to list Alice's workspaces? Should only see his own (already tested, but we can check that he doesn't see Alice's IDs)
    resp = list_workspaces(token_bob)
    bob_ws_ids = [ws["id"] for ws in resp.json()]
    assert alice_ws1 not in bob_ws_ids, "Bob should not see Alice's workspace"

    # ==============================
    # 7. Invalid Token
    # ==============================
    print_section("7. Invalid Token")

    invalid_token = "invalid.token.here"
    resp = requests.get(f"{BASE_URL}/workspaces", headers={"Authorization": f"Bearer {invalid_token}"})
    print("Invalid token list workspaces:", resp.status_code, resp.json())
    assert resp.status_code == 401

    # ==============================
    # 8. Get /me
    # ==============================
    print_section("8. /me endpoint")

    resp = get_me(token_alice)
    print("Alice /me:", resp.status_code, resp.json())
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"

    print("\n🎉 All tests passed (if no assertion errors)!")
    print("Backend is fully functional for the MVP.")

if __name__ == "__main__":
    # Ensure test.txt is cleaned up
    if os.path.exists("test.txt"):
        os.remove("test.txt")
    main()