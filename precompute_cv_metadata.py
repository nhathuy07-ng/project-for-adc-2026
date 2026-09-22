import os
import json
import needle
from pydantic import BaseModel, Field

class TemplateDescription(BaseModel):
    layout: str = Field(description="Concise 3-5 word description of the layout (e.g., 'Single-column standard', 'Two-column sidebar')")
    color_theme: str = Field(description="Concise 2-3 word description of the primary colors (e.g., 'Black and white', 'Navy and gray')")

def main():
    base_dir = "CVs"
    metadata = {}
    
    # Iterate through CV directories
    for category in os.listdir(base_dir):
        category_path = os.path.join(base_dir, category)
        if not os.path.isdir(category_path):
            continue
            
        for template in os.listdir(category_path):
            template_path = os.path.join(category_path, template)
            if not os.path.isdir(template_path):
                continue
                
            index_path = os.path.join(template_path, "index.html")
            css_path = os.path.join(template_path, "style.css")
            
            content = ""
            if os.path.exists(index_path):
                with open(index_path, "r", encoding="utf-8") as f:
                    content += f.read() + "\n"
            if os.path.exists(css_path):
                with open(css_path, "r", encoding="utf-8") as f:
                    content += f.read() + "\n"
                    
            if content:
                print(f"Extracting metadata for {template}...")
                try:
                    # Use needle default init
                    result = needle.extract(content, schema=TemplateDescription)
                    metadata[f"{category}/{template}"] = {
                        "name": template.replace("_", " ").replace("-", " "),
                        "layout": result.layout,
                        "color_theme": result.color_theme,
                        "path": template_path,
                        "index_path": index_path
                    }
                except Exception as e:
                    print(f"Failed to extract for {template}: {e}")
                    
    with open("cv_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print("Metadata pre-computed and saved to cv_metadata.json")

if __name__ == "__main__":
    main()
