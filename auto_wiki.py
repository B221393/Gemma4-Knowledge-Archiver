import subprocess
import os
import re
import time

# System Settings
BASE_DIR = r"C:\Users\Yuto\Documents\Obsidian_Research"
RULES_FILE = os.path.join(BASE_DIR, "WIKI_GENERATION_RULES.md")
INDEX_FILE = os.path.join(BASE_DIR, "00_WIKI_INDEX.md")
MODEL_NAME = "gemma4-wiki"

def call_ollama(prompt):
    """Call Gemma 4 and extract content (excluding Thinking process)"""
    process = subprocess.Popen(
        ["ollama", "run", MODEL_NAME],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    stdout, stderr = process.communicate(input=prompt)
    
    # Extract markdown content starting with #
    match = re.search(r'(#\s.*)', stdout, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback: remove thinking markers
    clean = re.sub(r'(?s)^.*?Thinking.*?\.\s*', '', stdout)
    return clean.strip()

def save_article(topic, content):
    """Save the article as a markdown file for Obsidian"""
    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic).replace(' ', '_')
    file_path = os.path.join(BASE_DIR, f"{safe_topic}.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Saved: {file_path}")
    
    # Update Index
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [[{safe_topic}]]\n")
    return content

def run_loop(start_topic):
    """Main generation loop with automatic next topic extraction"""
    current_topic = start_topic
    
    if not os.path.exists(RULES_FILE):
        print("Error: Rules file not found.")
        return

    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = f.read()

    print("--- Starting Wiki Generation Loop ---")
    while True:
        prompt = f"{rules}\n\n以下のトピックについて執筆してください。\n{current_topic}\n\n制約：即座に # 記事タイトル から開始してください。"
        print(f"Processing: {current_topic} ...")
        
        content = call_ollama(prompt)
        if content:
            save_article(current_topic, content)
            
            # Extract next topic from the content
            match = re.search(r'NEXT_WIKI_ARTICLE:\s*\[?([^\]\r\n]+)\]?', content)
            if match:
                current_topic = match.group(1).strip()
            else:
                current_topic = f"{current_topic} Deep Dive"
            
            print(f"Next Topic: {current_topic}")
        else:
            print("Failed. Retrying in 30s...")
            time.sleep(30)
            continue
            
        print("-" * 40)
        time.sleep(10)

if __name__ == "__main__":
    run_loop("設備台帳のRDB化とSQL基本操作")
