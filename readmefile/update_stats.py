import os
import sys
import json
import urllib.request
from collections import defaultdict

def fetch_json(url, token=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    # Accept header is required for commit searches
    req.add_header("Accept", "application/vnd.github.v3+json")
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
    
    # 1. Fetch User Profile Info (Public Repos, Followers)
    user_url = f"https://api.github.com/users/{username}"
    user_data = fetch_json(user_url, token)
    if not user_data:
        print("Failed to fetch user profile data.")
        return
        
    followers = user_data.get("followers", 0)
    public_repos_count = user_data.get("public_repos", 0)
    
    # 2. Fetch Repositories & Sum Stars
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = fetch_json(repos_url, token)
    if not repos:
        repos = []
        
    total_stars = 0
    lang_bytes = defaultdict(int)
    
    print(f"Analyzing {len(repos)} repositories...")
    for repo in repos:
        if repo.get("fork"):
            continue
        total_stars += repo.get("stargazers_count", 0)
        
        # Languages
        lang_url = repo.get("languages_url")
        if lang_url:
            langs = fetch_json(lang_url, token)
            if langs:
                for lang, bytes_count in langs.items():
                    lang_bytes[lang] += bytes_count
                    
    # 3. Query Commits, PRs, and Issues counts using Search API
    commits_url = f"https://api.github.com/search/commits?q=author:{username}"
    commits_data = fetch_json(commits_url, token)
    total_commits = commits_data.get("total_count", 0) if commits_data else 0
    
    prs_url = f"https://api.github.com/search/issues?q=author:{username}+type:pr"
    prs_data = fetch_json(prs_url, token)
    total_prs = prs_data.get("total_count", 0) if prs_data else 0
    
    issues_url = f"https://api.github.com/search/issues?q=author:{username}+type:issue"
    issues_data = fetch_json(issues_url, token)
    total_issues = issues_data.get("total_count", 0) if issues_data else 0
    
    # 4. Calculate Rank Score
    # Score formula similar to standard rating systems
    score = (total_commits * 0.5) + (total_stars * 4.0) + (total_prs * 2.0) + (total_issues * 1.0) + (followers * 3.0) + (public_repos_count * 0.5)
    
    if score >= 600:
        grade = "S+"
        progress_ratio = 1.0
    elif score >= 400:
        grade = "S"
        progress_ratio = 0.9
    elif score >= 250:
        grade = "A+"
        progress_ratio = 0.78
    elif score >= 120:
        grade = "A"
        progress_ratio = 0.65
    elif score >= 60:
        grade = "B+"
        progress_ratio = 0.5
    elif score >= 30:
        grade = "B"
        progress_ratio = 0.35
    else:
        grade = "C"
        progress_ratio = 0.2
        
    print(f"Stats: Commits={total_commits}, Stars={total_stars}, PRs={total_prs}, Issues={total_issues}, Score={score:.1f}, Grade={grade}")
    
    # ------------------ GENERATE STATS.SVG ------------------
    # Circle perimeter = 2 * pi * r = 2 * 3.14159 * 32 = 201.06
    r = 32
    perimeter = 2 * 3.14159265 * r
    dashoffset = perimeter * (1.0 - progress_ratio)
    
    stats_svg = f"""<svg width="485" height="195" viewBox="0 0 485 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Background panel matching your theme -->
  <rect x="0.5" y="0.5" width="484" height="194" rx="8" fill="#030712" stroke="#0D9488" stroke-width="1.5" />

  <!-- Card Title -->
  <text x="25" y="32" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="14" font-weight="bold">GitHub Statistics</text>

  <!-- Left Stats Grid -->
  <!-- Commits -->
  <text x="25" y="66" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Total Commits:</text>
  <text x="230" y="66" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_commits}</text>

  <!-- Stars -->
  <text x="25" y="92" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Total Stars:</text>
  <text x="230" y="92" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_stars}</text>

  <!-- Pull Requests -->
  <text x="25" y="118" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Pull Requests:</text>
  <text x="230" y="118" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_prs}</text>

  <!-- Issues -->
  <text x="25" y="144" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Total Issues:</text>
  <text x="230" y="144" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_issues}</text>

  <!-- Followers -->
  <text x="25" y="170" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Followers:</text>
  <text x="230" y="170" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{followers}</text>

  <!-- Right Grade Circle Infographic -->
  <g transform="translate(345, 100)">
    <!-- Base background ring -->
    <circle cx="0" cy="0" r="{r}" fill="none" stroke="rgba(16, 185, 129, 0.1)" stroke-width="5" />
    
    <!-- Progress Ring -->
    <circle cx="0" cy="0" r="{r}" fill="none" stroke="#10B981" stroke-width="5"
            stroke-dasharray="{perimeter:.2f}" stroke-dashoffset="{dashoffset:.2f}"
            stroke-linecap="round" transform="rotate(-90)" />
            
    <!-- Grade Character -->
    <text x="0" y="8" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="24" font-weight="bold" text-anchor="middle">{grade}</text>
    
    <!-- Score label -->
    <text x="0" y="52" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="10" font-weight="500" text-anchor="middle">RANKING</text>
  </g>
</svg>"""

    # ------------------ GENERATE LANGUAGES.SVG ------------------
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_langs[:5]
    others_bytes = sum(x[1] for x in sorted_langs[5:])
    
    total_bytes_count = sum(lang_bytes.values()) if lang_bytes else 1
    
    formatted_langs = []
    for lang, bytes_count in top_5:
        pct = (bytes_count / total_bytes_count) * 100
        formatted_langs.append((lang, pct))
        
    if others_bytes > 0:
        formatted_langs.append(("Others", (others_bytes / total_bytes_count) * 100))
        
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
        
    positions = [
        (31, 98, 42, 102, 125, 102),
        (180, 98, 191, 102, 250, 102),
        (320, 98, 331, 102, 405, 102),
        (31, 138, 42, 142, 125, 142),
        (180, 138, 191, 142, 250, 142),
        (320, 138, 331, 142, 405, 142)
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

    languages_svg = f"""<svg width="485" height="195" viewBox="0 0 485 195" xmlns="http://www.w3.org/2000/svg">
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

    # 5. Write both SVGs
    out_dir = "MahyudeenShahid/readmefile"
    if not os.path.exists(out_dir):
        out_dir = "readmefile"
    if not os.path.exists(out_dir):
        out_dir = "."
        
    stats_path = os.path.join(out_dir, "stats.svg")
    languages_path = os.path.join(out_dir, "languages.svg")
    
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(stats_svg)
    with open(languages_path, "w", encoding="utf-8") as f:
        f.write(languages_svg)
        
    print(f"[✓] Generated matching local SVGs:\n - {stats_path}\n - {languages_path}")

if __name__ == "__main__":
    main()
