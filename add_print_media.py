import json
import os
import re

with open("cv_metadata.json", "r") as f:
    cv_metadata = json.load(f)

print_media_css = """
@media print {
  body { 
    background: white !important; 
  }
  .resume, .page, .sheet, main, .container {
    margin: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    min-height: auto !important;
    box-shadow: none !important;
    padding: 10mm !important;
  }
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
"""

for key, info in cv_metadata.items():
    index_path = info["index_path"]
    print(f"Processing {index_path}...")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Check if @media print already exists
    if "@media print" not in html_content:
        # Inject right before </style>
        new_html = re.sub(r'</style>', f'{print_media_css}\n</style>', html_content, flags=re.IGNORECASE)
        
        if new_html != html_content:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(new_html)
            print(f"  ✅ Added @media print to {index_path}")
        else:
            print(f"  ⚠️ Could not find </style> tag in {index_path}")
    else:
        print(f"  ⏭️ @media print already exists in {index_path}")

print("Done!")
