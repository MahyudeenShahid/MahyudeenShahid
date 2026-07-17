import os
import sys
import json
import urllib.request
from collections import defaultdict

def fetch_json(url, token=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    username = "MahyudeenShahid"
    token = os.environ.get("GITHUB_TOKEN")
    
    # 1. Fetch all public repositories of the user
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = fetch_json(repos_url, token)
    if not repos:
        print("Failed to fetch repos.")
        return
        
    lang_bytes = defaultdict(int)
    
    # 2. Query language byte counts for each repo (excluding forks)
    print(f"Analyzing languages for {len(repos)} repositories...")
    for repo in repos:
        if repo.get("fork"):
            continue
        lang_url = repo.get("languages_url")
        if lang_url:
            langs = fetch_json(lang_url, token)
            if langs:
                for lang, bytes_count in langs.items():
                    lang_bytes[lang] += bytes_count
                    
    if not lang_bytes:
        print("No language statistics found.")
        return
        
    # Calculate exact percentages
    total_bytes = sum(lang_bytes.values())
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    
    # Aggregate top 5 languages, group everything else as "Others"
    top_5 = sorted_langs[:5]
    others_bytes = sum(x[1] for x in sorted_langs[5:])
    
    formatted_langs = []
    for lang, bytes_count in top_5:
        pct = (bytes_count / total_bytes) * 100
        formatted_langs.append((lang, pct))
        
    if others_bytes > 0:
        formatted_langs.append(("Others", (others_bytes / total_bytes) * 100))
        
    print("\nUpdated Language Statistics:")
    for lang, pct in formatted_langs:
        print(f" - {lang}: {pct:.1f}%")
        
    # 3. Generate updated themed SVG
    palette = ["#10B981", "#0D9488", "#34D399", "#10B981", "#0D9488", "#4B5563"]
    opacities = ["1", "1", "1", "0.6", "0.6", "1"]
    
    total_bar_width = 435
    svg_rects = []
    svg_legends = []
    
    current_x = 25
    for i, (lang, pct) in enumerate(formatted_langs):
        width = (pct / 100) * total_bar_width
        color = palette[i % len(palette)]
        opacity = opacities[i % len(opacities)]
        
        svg_rects.append(f'<rect x="{current_x:.2f}" y="55" width="{width:.2f}" height="10" fill="{color}" opacity="{opacity}" />')
        current_x += width
        
    # Positions grid (3 columns, 2 rows)
    positions = [
        (31, 98, 42, 102, 125, 102),   # Col 1, Row 1
        (180, 98, 191, 102, 250, 102), # Col 2, Row 1
        (320, 98, 331, 102, 405, 102), # Col 3, Row 1
        (31, 138, 42, 142, 125, 142),  # Col 1, Row 2
        (180, 138, 191, 142, 250, 142),# Col 2, Row 2
        (320, 138, 331, 142, 405, 142) # Col 3, Row 2
    ]
    
    for i, (lang, pct) in enumerate(formatted_langs):
        if i >= len(positions):
            break
        color = palette[i % len(palette)]
        opacity = opacities[i % len(opacities)]
        cx, cy, tx, ty, vx, vy = positions[i]
        
        svg_legends.append(f"""  <!-- {lang} -->
  <circle cx="{cx}" cy="{cy}" r="4" fill="{color}" opacity="{opacity}" />
  <text x="{tx}" y="{ty}" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">{lang}</text>
  <text x="{vx}" y="{vy}" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold">{pct:.1f}%</text>""")

    svg_content = f"""<svg width="485" height="195" viewBox="0 0 485 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="barClip">
      <rect x="25" y="55" width="435" height="10" rx="5" />
    </clipPath>
  </defs>

  <!-- Background panel matching your theme -->
  <rect x="0.5" y="0.5" width="484" height="194" rx="8" fill="#030712" stroke="#0D9488" stroke-width="1.5" />

  <!-- Card Title -->
  <text x="25" y="32" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="14" font-weight="bold">Top Languages</text>

  <!-- Progress Bar Group -->
  <g clip-path="url(#barClip)">
    {"    ".join(svg_rects)}
  </g>

{"".join(svg_legends)}
</svg>"""

    # Locate output directory
    out_dir = "MahyudeenShahid/readmefile"
    if not os.path.exists(out_dir):
        out_dir = "readmefile"
    if not os.path.exists(out_dir):
        out_dir = "."
        
    svg_path = os.path.join(out_dir, "languages.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[✓] Successfully re-compiled languages.svg at: {svg_path}")

if __name__ == "__main__":
    main()
