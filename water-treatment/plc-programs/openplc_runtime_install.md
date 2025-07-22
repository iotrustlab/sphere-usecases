
# 🖥️ OpenPLC Runtime Node Installation Guide

Follow the steps below to install and configure the OpenPLC runtime on a new node.

---

## 1. Install OpenPLC Runtime

```bash
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3
./install.sh linux
```

---

## 2. Upload and Compile Your Structured Text Program

### a. Transfer the `.st` file to the runtime node

From your local machine (e.g., JupyterHub):

```bash
scp your_program.st user@<node-ip>:~/OpenPLC_v3/webserver/st_files/
```

### b. Compile the program

```bash
cd ~/OpenPLC_v3/webserver/scripts/
./compile_program.sh your_program.st
```

---

## 3. Add Program to OpenPLC Database

Use the Python snippet below to register your program in the OpenPLC database:

```python
import sqlite3
import time

st_file = "your_program.st"  # <<<--- CHANGE THIS TO YOUR ACTUAL FILENAME
database = "openplc.db"

conn = sqlite3.connect(database)
cursor = conn.cursor()

cursor.execute("""
INSERT INTO Programs (Name, Description, File, Date_upload)
VALUES (?, ?, ?, ?)
""", (
    "Controller Program",         # Name shown in UI
    "Controller logic test",      # Description (optional)
    st_file,                      # Filename of your program
    int(time.time())              # Timestamp
))

conn.commit()
conn.close()
```

---

## 4. Enable Modbus Server and Auto-Run

Run the following SQLite command:

```bash
sqlite3 ~/OpenPLC_v3/webserver/openplc.db "
INSERT OR REPLACE INTO Settings (Key, Value) VALUES 
('storage_polling', 'enabled'),
('Modbus_port', '502'),
('Start_run_mode', 'true'),
('Modbus_server_enable', 'true');"
```

---

## 5. Start OpenPLC Runtime

```bash
cd ~/OpenPLC_v3
sudo ./start_openplc.sh
```

---
