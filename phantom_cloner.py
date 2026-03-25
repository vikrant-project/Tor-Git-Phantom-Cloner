#!/usr/bin/env python3
"""
UPA Company AI - Advanced Tor-Enabled Git Repository Cloner
A self-contained script for anonymous git cloning with IP rotation and multiple clone cycles
"""

import sys
import subprocess
import os
import json
from datetime import datetime

# ============================================================================
# PACKAGE INSTALLATION HANDLER
# ============================================================================
def install_packages():
    """Auto-install required packages if not present"""
    required_packages = {
        'flask': 'flask',
        'requests': 'requests',
        'git': 'gitpython'
    }
    
    print("🔧 Checking and installing required packages...")
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name} already installed")
        except ImportError:
            print(f"📦 Installing {package_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package_name])
            print(f"✓ {package_name} installed successfully")
    
    # Install PySocks for SOCKS proxy support
    try:
        import socks
        print("✓ PySocks already installed")
    except ImportError:
        print("📦 Installing PySocks...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "PySocks"])
        print("✓ PySocks installed successfully")
    
    print("✅ All packages ready!\n")

# Install packages before importing them
install_packages()

# Now import the packages
from flask import Flask, render_template_string, request, jsonify
import requests
import threading
import time
import shutil
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    TOR_PORT = 9050
    CLONE_DIR = "./cloned_repos"
    HOST = "0.0.0.0"
    PORT = 5000

# ============================================================================
# TOR MANAGER (Simplified - No Control Port Required)
# ============================================================================
class TorManager:
    def __init__(self):
        self.tor_process = None
        self.is_running = False
        
    def start_tor(self):
        """Start Tor service"""
        try:
            # Check if Tor is already running
            response = requests.get(
                "http://check.torproject.org/api/ip",
                proxies={
                    'http': f'socks5h://127.0.0.1:{Config.TOR_PORT}',
                    'https': f'socks5h://127.0.0.1:{Config.TOR_PORT}'
                },
                timeout=5
            )
            self.is_running = True
            print("✓ Tor is already running")
            return True
        except:
            pass
        
        # Try to start Tor
        try:
            print("🔄 Starting Tor service...")
            subprocess.Popen(
                ['tor'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)  # Wait for Tor to start
            self.is_running = True
            print("✓ Tor service started")
            return True
        except Exception as e:
            print(f"❌ Failed to start Tor: {e}")
            print("ℹ️  Please install Tor: sudo apt-get install tor")
            return False
    
    def get_current_ip(self):
        """Get current IP address through Tor"""
        try:
            response = requests.get(
                "http://check.torproject.org/api/ip",
                proxies={
                    'http': f'socks5h://127.0.0.1:{Config.TOR_PORT}',
                    'https': f'socks5h://127.0.0.1:{Config.TOR_PORT}'
                },
                timeout=10
            )
            data = response.json()
            return data.get('IP', 'Unknown')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def rotate_ip_simple(self):
        """Simple IP rotation by restarting connection"""
        try:
            # Kill and restart tor for IP rotation
            subprocess.run(['pkill', '-HUP', 'tor'], capture_output=True)
            time.sleep(3)  # Wait for new circuit
            return True
        except Exception as e:
            print(f"⚠️  IP rotation attempted: {e}")
            time.sleep(3)
            return True

# ============================================================================
# GIT CLONER WITH MULTIPLE CYCLES
# ============================================================================
class GitCloner:
    def __init__(self, tor_manager):
        self.tor_manager = tor_manager
        self.progress_data = {
            'status': 'idle',
            'current_ip': 'Not connected',
            'logs': [],
            'progress': 0,
            'repo_url': '',
            'clone_path': '',
            'current_cycle': 0,
            'total_cycles': 1,
            'cycle_history': []
        }
        self.stop_requested = False
    
    def add_log(self, message, level='info'):
        """Add log entry"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.progress_data['logs'].append({
            'time': timestamp,
            'message': message,
            'level': level
        })
        # Keep only last 100 logs
        if len(self.progress_data['logs']) > 100:
            self.progress_data['logs'] = self.progress_data['logs'][-100:]
    
    def delete_clone_directory(self, clone_path):
        """Delete the cloned repository directory"""
        try:
            if os.path.exists(clone_path):
                self.add_log(f"🗑️  Deleting previous clone: {os.path.basename(clone_path)}", 'warning')
                shutil.rmtree(clone_path)
                self.add_log(f"✅ Directory deleted successfully", 'success')
                return True
            return True
        except Exception as e:
            self.add_log(f"❌ Failed to delete directory: {str(e)}", 'error')
            return False
    
    def clone_single_cycle(self, repo_url, clone_path, cycle_num):
        """Clone repository for a single cycle"""
        try:
            self.add_log(f"🔄 Cycle {cycle_num}/{self.progress_data['total_cycles']}: Rotating IP...", 'info')
            
            # Rotate IP before each clone
            self.tor_manager.rotate_ip_simple()
            time.sleep(2)
            
            # Get current IP
            current_ip = self.tor_manager.get_current_ip()
            self.progress_data['current_ip'] = current_ip
            self.add_log(f"🌐 Cycle {cycle_num} IP: {current_ip}", 'success')
            
            # Delete old clone if exists
            if os.path.exists(clone_path):
                if not self.delete_clone_directory(clone_path):
                    return False
            
            # Configure git to use Tor proxy
            proxy_url = f'socks5h://127.0.0.1:{Config.TOR_PORT}'
            self.add_log(f"📥 Cloning repository (Cycle {cycle_num})...", 'info')
            
            # Use git clone with http proxy
            git_config = [
                'git', '-c', f'http.proxy={proxy_url}',
                '-c', f'https.proxy={proxy_url}',
                'clone', '--progress', repo_url, clone_path
            ]
            
            process = subprocess.Popen(
                git_config,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor clone progress
            for line in process.stdout:
                if self.stop_requested:
                    process.kill()
                    return False
                    
                line = line.strip()
                if line:
                    self.add_log(f"git: {line}", 'info')
            
            process.wait()
            
            if process.returncode == 0:
                self.add_log(f"✅ Cycle {cycle_num} completed successfully!", 'success')
                # Record cycle history
                self.progress_data['cycle_history'].append({
                    'cycle': cycle_num,
                    'ip': current_ip,
                    'status': 'success',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                return True
            else:
                self.add_log(f"❌ Cycle {cycle_num} failed with return code: {process.returncode}", 'error')
                self.progress_data['cycle_history'].append({
                    'cycle': cycle_num,
                    'ip': current_ip,
                    'status': 'failed',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                return False
                
        except Exception as e:
            self.add_log(f"❌ Cycle {cycle_num} error: {str(e)}", 'error')
            return False
    
    def clone_repository_multiple(self, repo_url, num_cycles=1):
        """Clone repository multiple times with IP rotation"""
        self.stop_requested = False
        self.progress_data['status'] = 'running'
        self.progress_data['repo_url'] = repo_url
        self.progress_data['progress'] = 0
        self.progress_data['logs'] = []
        self.progress_data['total_cycles'] = num_cycles
        self.progress_data['current_cycle'] = 0
        self.progress_data['cycle_history'] = []
        
        try:
            # Create clone directory
            Path(Config.CLONE_DIR).mkdir(exist_ok=True)
            
            # Extract repo name
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = os.path.join(Config.CLONE_DIR, repo_name)
            self.progress_data['clone_path'] = clone_path
            
            self.add_log(f"📦 Starting {num_cycles} clone cycle(s) for: {repo_name}", 'info')
            self.add_log(f"🔒 All clones will be performed anonymously through Tor", 'info')
            
            # Perform multiple clone cycles
            successful_cycles = 0
            for cycle in range(1, num_cycles + 1):
                if self.stop_requested:
                    self.add_log(f"⚠️  Clone operation stopped by user", 'warning')
                    break
                
                self.progress_data['current_cycle'] = cycle
                
                self.add_log(f"\n{'='*50}", 'info')
                self.add_log(f"🚀 Starting Cycle {cycle}/{num_cycles}", 'info')
                self.add_log(f"{'='*50}", 'info')
                
                # Clone for this cycle
                success = self.clone_single_cycle(repo_url, clone_path, cycle)
                
                if success:
                    successful_cycles += 1
                
                # Update progress
                self.progress_data['progress'] = int((cycle / num_cycles) * 100)
                
                # Wait a bit between cycles (except for the last one)
                if cycle < num_cycles and not self.stop_requested:
                    self.add_log(f"⏳ Waiting before next cycle...", 'info')
                    time.sleep(2)
            
            # Final summary
            self.add_log(f"\n{'='*50}", 'info')
            self.add_log(f"📊 SUMMARY: {successful_cycles}/{num_cycles} cycles successful", 'success')
            self.add_log(f"{'='*50}", 'info')
            
            if successful_cycles == num_cycles:
                self.progress_data['status'] = 'completed'
                self.add_log(f"🎉 All cycles completed! Final clone at: {clone_path}", 'success')
            elif successful_cycles > 0:
                self.progress_data['status'] = 'partial'
                self.add_log(f"⚠️  Partial success. Final clone at: {clone_path}", 'warning')
            else:
                self.progress_data['status'] = 'failed'
                self.add_log(f"❌ All cycles failed", 'error')
            
            self.progress_data['progress'] = 100
            return successful_cycles > 0
                
        except Exception as e:
            self.add_log(f"❌ Fatal error: {str(e)}", 'error')
            self.progress_data['status'] = 'failed'
            self.progress_data['progress'] = 0
            return False
    
    def stop_cloning(self):
        """Request to stop the cloning operation"""
        self.stop_requested = True
        self.add_log("⚠️  Stop requested...", 'warning')
    
    def get_progress(self):
        """Get current progress data"""
        return self.progress_data

# ============================================================================
# EMBEDDED HTML TEMPLATE
# ============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPA Company AI - Advanced Tor Git Cloner</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .input-group input[type="text"],
        .input-group input[type="number"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .input-row {
            display: grid;
            grid-template-columns: 1fr 200px;
            gap: 15px;
            align-items: end;
        }
        
        .btn {
            padding: 14px 28px;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 100%;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: 1fr 150px;
            gap: 10px;
        }
        
        .status-bar {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .status-item {
            padding: 10px;
            background: white;
            border-radius: 6px;
        }
        
        .status-label {
            font-size: 0.85rem;
            color: #888;
            margin-bottom: 5px;
        }
        
        .status-value {
            font-size: 1.1rem;
            color: #667eea;
            font-weight: 600;
        }
        
        .progress-container {
            margin: 20px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 35px;
            background: #e0e0e0;
            border-radius: 17px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .logs-container {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #333;
        }
        
        .log-time {
            color: #888;
            margin-right: 10px;
        }
        
        .log-message {
            color: #e0e0e0;
        }
        
        .log-info { color: #4fc3f7; }
        .log-success { color: #66bb6a; }
        .log-warning { color: #ffa726; }
        .log-error { color: #ef5350; }
        
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .status-idle { background: #e0e0e0; color: #555; }
        .status-running { background: #64b5f6; color: white; }
        .status-completed { background: #66bb6a; color: white; }
        .status-partial { background: #ffa726; color: white; }
        .status-failed { background: #ef5350; color: white; }
        
        .cycle-history {
            margin-top: 15px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
        }
        
        .cycle-history h4 {
            margin-bottom: 10px;
            color: #555;
        }
        
        .cycle-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .cycle-success { border-left: 4px solid #66bb6a; }
        .cycle-failed { border-left: 4px solid #ef5350; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .info-box p {
            margin: 5px 0;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 UPA Company AI</h1>
            <p>Advanced Tor-Enabled Git Cloner with Multi-Cycle Support</p>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 20px; color: #667eea;">Clone Repository</h2>
            
            <div class="info-box">
                <p><strong>🔄 Multi-Cycle Cloning:</strong> Clone the same repository multiple times with IP rotation</p>
                <p><strong>🗑️ Auto-Delete:</strong> Previous clones are automatically deleted before starting new ones</p>
                <p><strong>🔒 Anonymous:</strong> Each cycle uses a different Tor IP address</p>
            </div>
            
            <div class="input-group">
                <label>GitHub Repository URL</label>
                <input type="text" id="repoUrl" placeholder="https://github.com/username/repository.git">
            </div>
            
            <div class="input-group">
                <label>Number of Clone Cycles (1-1000000000000000)</label>
                <input type="number" id="numCycles" value="1" min="1" max="1000000000000000">
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" id="cloneBtn" onclick="startClone()">
                    🚀 Start Clone
                </button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopClone()" style="display: none;">
                    ⏹️ Stop
                </button>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 20px; color: #667eea;">Status</h2>
            
            <div class="status-bar">
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-label">Status</div>
                        <div class="status-value">
                            <span id="statusBadge" class="status-badge status-idle">Idle</span>
                        </div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Current IP</div>
                        <div class="status-value" id="currentIp">Not connected</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Repository</div>
                        <div class="status-value" id="repoName">-</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Cycle Progress</div>
                        <div class="status-value" id="cycleProgress">0/0</div>
                    </div>
                </div>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill" style="width: 0%">
                        <span id="progressText">0%</span>
                    </div>
                </div>
            </div>
            
            <div class="cycle-history" id="cycleHistory" style="display: none;">
                <h4>📊 Cycle History</h4>
                <div id="cycleHistoryList"></div>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 20px; color: #667eea;">Live Logs</h2>
            <div class="logs-container" id="logsContainer">
                <div class="log-entry">
                    <span class="log-time">00:00:00</span>
                    <span class="log-message log-info">System ready. Enter a repository URL to begin.</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        
        function startClone() {
            const repoUrl = document.getElementById('repoUrl').value.trim();
            const numCycles = parseInt(document.getElementById('numCycles').value);
            const cloneBtn = document.getElementById('cloneBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            if (!repoUrl) {
                alert('Please enter a repository URL');
                return;
            }
            
            if (numCycles < 1 || numCycles > 1000000000000000) {
                alert('Please enter a number between 1 and 1000000000000000');
                return;
            }
            
            cloneBtn.disabled = true;
            cloneBtn.textContent = '⏳ Cloning...';
            stopBtn.style.display = 'block';
            
            fetch('/clone', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({repo_url: repoUrl, num_cycles: numCycles})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    startProgressUpdate();
                } else {
                    alert('Failed to start clone: ' + data.message);
                    cloneBtn.disabled = false;
                    cloneBtn.textContent = '🚀 Start Clone';
                    stopBtn.style.display = 'none';
                }
            })
            .catch(error => {
                alert('Error: ' + error);
                cloneBtn.disabled = false;
                cloneBtn.textContent = '🚀 Start Clone';
                stopBtn.style.display = 'none';
            });
        }
        
        function stopClone() {
            if (confirm('Are you sure you want to stop the cloning operation?')) {
                fetch('/stop', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        console.log('Stop requested');
                    });
            }
        }
        
        function startProgressUpdate() {
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(updateProgress, 500);
        }
        
        function updateProgress() {
            fetch('/progress')
                .then(response => response.json())
                .then(data => {
                    // Update status badge
                    const statusBadge = document.getElementById('statusBadge');
                    statusBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    statusBadge.className = 'status-badge status-' + data.status;
                    if (data.status === 'running') {
                        statusBadge.classList.add('pulse');
                    }
                    
                    // Update IP
                    document.getElementById('currentIp').textContent = data.current_ip;
                    
                    // Update repo name
                    if (data.repo_url) {
                        const repoName = data.repo_url.split('/').pop().replace('.git', '');
                        document.getElementById('repoName').textContent = repoName;
                    }
                    
                    // Update cycle progress
                    document.getElementById('cycleProgress').textContent = 
                        data.current_cycle + '/' + data.total_cycles;
                    
                    // Update progress bar
                    const progressFill = document.getElementById('progressFill');
                    const progressText = document.getElementById('progressText');
                    const progress = Math.round(data.progress);
                    progressFill.style.width = progress + '%';
                    progressText.textContent = progress + '%';
                    
                    // Update cycle history
                    if (data.cycle_history && data.cycle_history.length > 0) {
                        document.getElementById('cycleHistory').style.display = 'block';
                        const historyList = document.getElementById('cycleHistoryList');
                        historyList.innerHTML = '';
                        data.cycle_history.forEach(cycle => {
                            const cycleDiv = document.createElement('div');
                            cycleDiv.className = 'cycle-item cycle-' + cycle.status;
                            cycleDiv.innerHTML = `
                                <span><strong>Cycle ${cycle.cycle}</strong> @ ${cycle.time}</span>
                                <span>IP: ${cycle.ip}</span>
                                <span class="status-badge status-${cycle.status === 'success' ? 'completed' : 'failed'}">
                                    ${cycle.status}
                                </span>
                            `;
                            historyList.appendChild(cycleDiv);
                        });
                    }
                    
                    // Update logs
                    const logsContainer = document.getElementById('logsContainer');
                    logsContainer.innerHTML = '';
                    data.logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.innerHTML = `
                            <span class="log-time">${log.time}</span>
                            <span class="log-message log-${log.level}">${log.message}</span>
                        `;
                        logsContainer.appendChild(logEntry);
                    });
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                    
                    // Re-enable button if completed or failed
                    if (data.status !== 'running') {
                        const cloneBtn = document.getElementById('cloneBtn');
                        const stopBtn = document.getElementById('stopBtn');
                        cloneBtn.disabled = false;
                        cloneBtn.textContent = '🚀 Start Clone';
                        stopBtn.style.display = 'none';
                        clearInterval(updateInterval);
                    }
                });
        }
        
        // Check IP on load
        window.onload = function() {
            fetch('/check-ip')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('currentIp').textContent = data.ip;
                });
        };
    </script>
</body>
</html>
"""

# ============================================================================
# FLASK APPLICATION
# ============================================================================
app = Flask(__name__)
tor_manager = TorManager()
git_cloner = GitCloner(tor_manager)
clone_thread = None

@app.route('/')
def index():
    """Serve main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/check-ip')
def check_ip():
    """Get current IP address"""
    ip = tor_manager.get_current_ip()
    return jsonify({'ip': ip})

@app.route('/clone', methods=['POST'])
def clone():
    """Start cloning a repository"""
    global clone_thread
    
    data = request.json
    repo_url = data.get('repo_url')
    num_cycles = data.get('num_cycles', 1)
    
    if not repo_url:
        return jsonify({'success': False, 'message': 'No repository URL provided'})
    
    # Validate number of cycles
    try:
        num_cycles = int(num_cycles)
        if num_cycles < 1 or num_cycles > 1000000000000000:
            return jsonify({'success': False, 'message': 'Number of cycles must be between 1 and 1000000000000000'})
    except:
        return jsonify({'success': False, 'message': 'Invalid number of cycles'})
    
    # Check if already cloning
    if clone_thread and clone_thread.is_alive():
        return jsonify({'success': False, 'message': 'A clone operation is already in progress'})
    
    # Start clone in background thread
    clone_thread = threading.Thread(
        target=git_cloner.clone_repository_multiple,
        args=(repo_url, num_cycles)
    )
    clone_thread.start()
    
    return jsonify({'success': True, 'message': f'Clone started with {num_cycles} cycle(s)'})

@app.route('/stop', methods=['POST'])
def stop():
    """Stop the current cloning operation"""
    git_cloner.stop_cloning()
    return jsonify({'success': True, 'message': 'Stop requested'})

@app.route('/progress')
def progress():
    """Get current progress"""
    return jsonify(git_cloner.get_progress())

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Main function"""
    print("=" * 70)
    print("  UPA COMPANY AI - ADVANCED TOR GIT CLONER")
    print("  Multi-Cycle Cloning with Automatic IP Rotation")
    print("=" * 70)
    print()
    
    # Start Tor
    if not tor_manager.start_tor():
        print("\n⚠️  Warning: Tor failed to start. Please ensure Tor is installed.")
        print("   Installation: sudo apt-get install tor")
        print("   The application will run, but cloning may not work.\n")
    
    # Get initial IP
    print(f"🌐 Current IP: {tor_manager.get_current_ip()}\n")
    
    # Create clone directory
    Path(Config.CLONE_DIR).mkdir(exist_ok=True)
    print(f"📁 Clone directory: {os.path.abspath(Config.CLONE_DIR)}\n")
    
    # Start Flask server
    print(f"🚀 Starting web server on http://{Config.HOST}:{Config.PORT}")
    print(f"   Open your browser and navigate to: http://localhost:{Config.PORT}")
    print("\n   🔄 NEW FEATURE: Multi-cycle cloning with auto-delete & IP rotation!")
    print("   Press Ctrl+C to stop the server\n")
    print("=" * 70)
    
    app.run(host=Config.HOST, port=Config.PORT, debug=False, threaded=True)

if __name__ == '__main__':
    main()

