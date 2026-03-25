# 🔒 Tor Git Phantom Cloner v3.0
> **The ultimate anonymous repository cloner with automated IP rotation and multi-cycle synchronization.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Tor](https://img.shields.io/badge/Network-Tor%20Network-purple?logo=tor-project)](https://www.torproject.org/)
[![Flask](https://img.shields.io/badge/UI-Flask%20Web%20Dashboard-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Status](https://img.shields.io/badge/Status-Advanced-success)](#)

---

## 🔍 What is this Code?
**Tor Git Phantom Cloner** is a professional-grade automation tool designed for secure, anonymous Git operations. It integrates a **Flask-powered Web UI** with a **Tor proxy manager** to allow users to clone repositories repeatedly under different global identities. 

By wrapping Git commands in a SOCKS5h proxy layer, it ensures that your true IP address is never exposed to the Git host (GitHub, GitLab, Bitbucket).

---

## 🚀 Why Use It?
Standard Git cloning reveals your identity and location. This tool provides:
* **True Anonymity:** Every clone cycle passes through the Tor network.
* **IP Rotation Engine:** Automatically sends a `HUP` signal to Tor to request a new circuit (and a new IP) between every clone cycle.
* **Mass Synchronization:** Clone a single repository up to **1 Quadrillion** times for testing, mirroring, or load-analysis purposes.
* **Auto-Cleanup:** Automatically wipes the local directory before each cycle to prevent "already exists" errors.

---

## 💎 Importance
In cybersecurity research and decentralized development:
1.  **Anti-Tracking:** Prevents Git hosting providers from profiling your development machine's IP.
2.  **Traffic Analysis:** Useful for researchers studying how Git servers handle high-frequency connections from diverse geographic locations.
3.  **Zero-Configuration:** Includes a built-in package handler that auto-installs `Flask`, `Requests`, and `GitPython` on the first launch.

---

## ⚙️ How It Works
The system architecture follows a **Cyclic Proxy Pipeline**:



1.  **Web Handshake:** User enters a Repo URL and Cycle count in the high-end Glassmorphism dashboard.
2.  **Tor Initialization:** The script checks for a local Tor instance or spawns a new process on Port 9050.
3.  **The Phantom Cycle:**
    * **IP Rotation:** Signals Tor to switch identities.
    * **Verification:** Queries the Tor Project API to confirm a secure connection.
    * **Atomic Clone:** Executes `git clone` with `-c http.proxy` injected directly into the command string.
4.  **Live Monitoring:** Progress and Git status messages are streamed to the Web UI via JSON polling.

---

## 📊 Comparison: Why Phantom Cloner?

| Feature | Standard Git | VPN Cloner | Tor Phantom Cloner |
| :--- | :--- | :--- | :--- |
| **IP Exposure** | Full Exposure | VPN Provider Sees | **Zero Exposure** |
| **Rotation** | Manual | Manual/Slow | **Automated & Instant** |
| **Automation** | CLI Only | Scripted | **Full Web Dashboard** |
| **Clean-up** | Manual | Manual | **Automatic Purge** |
| **Scalability** | 1 at a time | Limited | **Multi-Quadrillion Cycles** |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Python 3.8+**
* **Tor Browser/Service:** Must be installed on your system.
  * *Linux:* `sudo apt-get install tor`
  * *Windows:* Install Tor Browser and leave it open.

### 2. Clone & Launch
```bash
git clone https://github.com/vikrant-project/Tor-Git-Phantom-Cloner
cd Tor-Git-Phantom-Cloner
python3 phantom_cloner.py
```

### 3. Usage
1.  Navigate to `http://localhost:5000` in your browser.
2.  Input the target `.git` URL.
3.  Set your cycle count (e.g., `10` for 10 unique anonymous clones).
4.  Monitor the **Live Progress Bar** and **Log Console**.

---

## 🎨 High-End UI Features
* **Glassmorphism Design:** A modern, sleek web interface with gradient backgrounds.
* **Live Status Badges:** Visual indicators for `Idle`, `Running`, and `Completed` states.
* **Cycle History:** A dedicated log table showing the timestamp and IP address used for every single clone.

---
**Disclaimer:** This tool is for educational, research, and authorized testing purposes only. Users are responsible for adhering to the Terms of Service of Git hosting providers.

