import subprocess
import os
import re
import time
import sys

# System Settings
BASE_DIR = r"C:\Users\Yuto\Documents\Obsidian_Research"
RULES_FILE = os.path.join(BASE_DIR, "WIKI_GENERATION_RULES.md")
INDEX_FILE = os.path.join(BASE_DIR, "00_WIKI_INDEX.md")
MODEL_NAME = "gemma4-wiki"

def call_ollama(prompt):
    """Call Gemma 4 and filter output (Timeout: 20min)"""
    input_bytes = prompt.encode("utf-8")
    process = subprocess.Popen(
        ["ollama", "run", MODEL_NAME],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )
    try:
        stdout_bytes, stderr_bytes = process.communicate(input=input_bytes, timeout=1200)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout_bytes, stderr_bytes = process.communicate()
    
    stdout = stdout_bytes.decode("utf-8", errors="ignore")
    # Clean Thinking process
    clean = re.sub(r'(?s)<\|think\|>.*?<\|done\|>', '', stdout)
    clean = re.sub(r'(?s)Thinking.*?\.\.\.', '', clean)
    match = re.search(r'(#\s.*)', clean, re.DOTALL)
    return match.group(1).strip() if match else clean.strip()

def save_article(topic, content):
    """Save with BOM for Obsidian and Sync to GitHub"""
    title_match = re.search(r'^#\s*(.*)', content)
    final_topic = title_match.group(1).strip() if title_match else topic
    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', final_topic).strip().replace(' ', '_')
    file_path = os.path.join(BASE_DIR, f"{safe_topic}.md")
    
    # Save Locally
    with open(file_path, "w", encoding="utf-8-sig") as f:
        f.write(content)
    
    # Update Index
    with open(INDEX_FILE, "a+", encoding="utf-8-sig") as f:
        f.seek(0)
        if f"[[{safe_topic}]]" not in f.read():
            f.write(f"- [[{safe_topic}]]\n")
    
    # GitHub Push
    print(f"Syncing {safe_topic} to GitHub...")
    subprocess.run(["git", "add", "."], cwd=BASE_DIR)
    subprocess.run(["git", "commit", "-m", f"Auto-Gen: {safe_topic}"], cwd=BASE_DIR)
    subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR)
    return final_topic

def notify_completion(count, last_topic):
    """Silent notification via Desktop and Report"""
    msg = f"Learning session complete: {count} articles built."
    ps_cmd = f"& {{ [reflection.assembly]::loadwithpartialname('System.Windows.Forms'); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.BalloonTipTitle = 'Gemma 4 Wiki'; $n.BalloonTipText = '{msg}'; $n.Visible = $True; $n.ShowBalloonTip(5000); }}"
    subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
    
    report_path = os.path.join(BASE_DIR, "COMPLETION_REPORT.md")
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(f"# Auto-Learning Report ({time.strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        f.write(f"- **Count**: {count}\n- **Last Topic**: [[{last_topic}]]\n\nSync to GitHub complete.")

def run_stepwise(topic):
    if not os.path.exists(RULES_FILE): return None
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = f.read()
    
    print(f"--- Processing: {topic} ---")
    # Two-stage quality generation
    prompt1 = f"{rules}\n\nTopic: {topic}\nTask: Initial rigorous drafting."
    draft = call_ollama(prompt1)
    if not draft: return None
    
    prompt2 = f"{rules}\n\nRedraft this for professional exam preparation:\n{draft}"
    final = call_ollama(prompt2)
    
    if final:
        actual_t = save_article(topic, final)
        match = re.search(r'NEXT_WIKI_ARTICLE:\s*\[?([^\]\r\n]+)\]?', final)
        return match.group(1).strip() if match else f"{actual_t} Deep Dive"
    return None

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    # Get current start topic from index or guide
    current_topic = "材料力学：はりの曲げ応力と断面二次モーメントの導出"
    count = 0
    for i in range(limit):
        next_t = run_stepwise(current_topic)
        if next_t:
            count += 1
            last_topic = current_topic
            current_topic = next_t
            time.sleep(5)
        else: break
    if count > 0: notify_completion(count, last_topic)
