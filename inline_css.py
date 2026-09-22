import json
import os
import re

with open("cv_metadata.json", "r") as f:
    cv_metadata = json.load(f)

for key, info in cv_metadata.items():
    index_path = info["index_path"]
    template_dir = os.path.dirname(index_path)
    print(f"Processing {index_path}...")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    def replacer(match):
        css_file = match.group(1)
        css_path = os.path.join(template_dir, css_file)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as cf:
                css_content = cf.read()
            return f"<style>\n{css_content}\n</style>"
        else:
            print(f"  ⚠️ WARNING: CSS file not found: {css_path}")
            return match.group(0)
            
    # Regex to match <link rel="stylesheet" href="..."> and variations
    pattern1 = r'<link\s+(?:[^>]*\s+)?rel=["\']stylesheet["\']\s+(?:[^>]*\s+)?href=["\']([^"\']+\.css)["\'][^>]*>'
    pattern2 = r'<link\s+(?:[^>]*\s+)?href=["\']([^"\']+\.css)["\']\s+(?:[^>]*\s+)?rel=["\']stylesheet["\'][^>]*>'
    
    new_html = re.sub(pattern1, replacer, html_content, flags=re.IGNORECASE)
    if new_html == html_content:
        new_html = re.sub(pattern2, replacer, new_html, flags=re.IGNORECASE)
        
    if new_html != html_content:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"  ✅ Inlined CSS for {index_path}")
    else:
        print(f"  ⚠️ No CSS link replaced for {index_path}")

print("Done!")
