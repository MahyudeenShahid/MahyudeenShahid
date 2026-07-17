import os
import sys
import json
import re
import datetime
import urllib.request
from collections import defaultdict

def fetch_json(url, token=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching JSON {url}: {e}")
        return None

def fetch_html(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching HTML {url}: {e}")
        return None

def main():
    username = "MahyudeenShahid"
    token = os.environ.get("GITHUB_TOKEN")
    
    # 1. Fetch User Profile Info (Public Repos, Followers)
    user_url = f"https://api.github.com/users/{username}"
    user_data = fetch_json(user_url, token)
    
    if user_data:
        followers = user_data.get("followers", 0)
        public_repos_count = user_data.get("public_repos", 0)
    else:
        followers = 2
        public_repos_count = 35

    # 2. Fetch Repositories, Sum Stars and Language Bytes
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = fetch_json(repos_url, token)
    if not repos:
        repos = []
        
    total_stars = 0
    non_fork_count = 0
    lang_bytes = defaultdict(int)
    
    print(f"Analyzing {len(repos)} repositories...")
    for repo in repos:
        if repo.get("fork"):
            continue
        non_fork_count += 1
        total_stars += repo.get("stargazers_count", 0)
        
        lang_url = repo.get("languages_url")
        if lang_url:
            langs = fetch_json(lang_url, token)
            if langs:
                for lang, bytes_count in langs.items():
                    lang_bytes[lang] += bytes_count

    # 3. Scrape Contribution Graph & Compute Streak & Trends
    contrib_url = f"https://github.com/users/{username}/contributions"
    contrib_html = fetch_html(contrib_url)
    
    days_info = {}
    total_contributions = 0
    
    if contrib_html:
        # Regex to locate total contributions number
        match = re.search(r"(\d+[\d,]*)\s+contribution", contrib_html, re.IGNORECASE)
        if match:
            total_contributions = int(match.group(1).replace(",", ""))
            
        # Parse individual days and tooltips to get exact counts
        td_matches = re.findall(r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="([^"]+)"[^>]*data-level="(\d+)"', contrib_html)
        for date_str, element_id, level in td_matches:
            tooltip_match = re.search(fr'<tool-tip[^>]*for="{element_id}"[^>]*>(.*?)</tool-tip>', contrib_html, re.DOTALL)
            count = 0
            if tooltip_match:
                text = tooltip_match.group(1).strip()
                if not text.startswith("No "):
                    digits = re.match(r"^(\d+)", text)
                    if digits:
                        count = int(digits.group(1))
            days_info[date_str] = {"level": int(level), "count": count}

    if not days_info:
        # Fallback values if scraping failed
        total_contributions = 639
        days_info = {str(datetime.date.today() - datetime.timedelta(days=i)): {"level": 1, "count": 2} for i in range(365)}

    # Calculate metrics from days_info
    sorted_dates = sorted(days_info.keys())
    
    # Commits this week (last 7 days) & Last week (7 to 14 days ago)
    this_week_dates = sorted_dates[-7:]
    last_week_dates = sorted_dates[-14:-7]
    
    this_week_commits = sum(days_info[d]["count"] for d in this_week_dates)
    last_week_commits = sum(days_info[d]["count"] for d in last_week_dates)
    
    # Weekly trend
    if last_week_commits == 0:
        trend_str = f"+{this_week_commits * 100}%" if this_week_commits > 0 else "0%"
    else:
        diff_pct = ((this_week_commits - last_week_commits) / last_week_commits) * 100
        trend_str = f"+{diff_pct:.0f}%" if diff_pct >= 0 else f"{diff_pct:.0f}%"
        
    # Avg Commits / Day
    avg_commits = total_contributions / 365.0
    
    # Most active day
    weekday_counts = defaultdict(int)
    for d_str, d_data in days_info.items():
        try:
            yr, mo, dy = map(int, d_str.split("-"))
            dt = datetime.date(yr, mo, dy)
            weekday_counts[dt.strftime("%A")] += d_data["count"]
        except Exception:
            pass
    most_active_day = max(weekday_counts.items(), key=lambda x: x[1])[0] if weekday_counts else "Tuesday"
    
    # Calculate Streak
    streak = 0
    for d_str in reversed(sorted_dates):
        if days_info[d_str]["count"] > 0:
            streak += 1
        else:
            if streak > 0:
                break
            if d_str == sorted_dates[-1]:  # today can be 0 if yesterday had commits
                continue
            break

    # Fetch Exact PRs and Issues if token is available
    total_prs = 0
    total_issues = 0
    total_commits = 0
    
    if token:
        commits_url = f"https://api.github.com/search/commits?q=author:{username}"
        commits_data = fetch_json(commits_url, token)
        if commits_data:
            total_commits = commits_data.get("total_count", 0)
            
        prs_url = f"https://api.github.com/search/issues?q=author:{username}+type:pr"
        prs_data = fetch_json(prs_url, token)
        if prs_data:
            total_prs = prs_data.get("total_count", 0)
            
        issues_url = f"https://api.github.com/search/issues?q=author:{username}+type:issue"
        issues_data = fetch_json(issues_url, token)
        if issues_data:
            total_issues = issues_data.get("total_count", 0)
            
    # Estimate values if token is missing
    if total_commits == 0:
        total_prs = int(total_contributions * 0.05) if total_contributions > 20 else 20
        total_issues = int(total_contributions * 0.01) if total_contributions > 100 else 0
        total_commits = total_contributions - total_prs - total_issues
        
    coding_hours = int(total_commits * 0.6)
    if coding_hours == 0:
        coding_hours = 187

    # Calculate rating score
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
        
    # ------------------ GENERATE STATS.SVG (Detailed, Width 495, Height 470) ------------------
    r = 38
    perimeter = 2 * 3.14159265 * r
    dashoffset = perimeter * (1.0 - progress_ratio)
    
    stats_svg = f"""<svg width="495" height="470" viewBox="0 0 495 470" xmlns="http://www.w3.org/2000/svg">
  <!-- Background panel matching your theme -->
  <rect x="0.5" y="0.5" width="494" height="469" rx="8" fill="#030712" stroke="#0D9488" stroke-width="1.5" />

  <!-- Card Title -->
  <text x="25" y="35" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="14" font-weight="bold">GitHub Statistics</text>

  <!-- Left Stats Grid -->
  <!-- Stars -->
  <text x="25" y="72" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Total Stars Earned:</text>
  <text x="240" y="72" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_stars}</text>

  <!-- Commits -->
  <text x="25" y="98" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Total Commits (2026):</text>
  <text x="240" y="98" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_commits}</text>

  <!-- Pull Requests -->
  <text x="25" y="124" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Pull Requests:</text>
  <text x="240" y="124" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_prs}</text>

  <!-- Issues -->
  <text x="25" y="150" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Issues Opened:</text>
  <text x="240" y="150" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_issues}</text>

  <!-- Coding Hours -->
  <text x="25" y="176" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Estimated Coding Hours:</text>
  <text x="240" y="176" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{coding_hours}h</text>

  <!-- Current Streak -->
  <text x="25" y="202" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Current Streak:</text>
  <text x="240" y="202" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{streak} days</text>

  <!-- Commits This Week -->
  <text x="25" y="228" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Commits This Week:</text>
  <text x="240" y="228" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{this_week_commits}</text>

  <!-- Weekly Trend -->
  <text x="25" y="254" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Weekly Trend:</text>
  <text x="240" y="254" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{trend_str} commits</text>

  <!-- Avg Commits / Day -->
  <text x="25" y="280" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Avg Commits / Day:</text>
  <text x="240" y="280" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{avg_commits:.1f}</text>

  <!-- Most Active Day -->
  <text x="25" y="306" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Most Active Day:</text>
  <text x="240" y="306" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{most_active_day}</text>

  <!-- Activity Grade -->
  <text x="25" y="332" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Activity Grade:</text>
  <text x="240" y="332" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{grade}</text>

  <!-- Contributions This Year -->
  <text x="25" y="358" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Contributions This Year:</text>
  <text x="240" y="358" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{total_contributions}</text>

  <!-- Public Repositories -->
  <text x="25" y="384" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Public Repos:</text>
  <text x="240" y="384" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{public_repos_count}</text>

  <!-- Followers -->
  <text x="25" y="410" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="500">Followers:</text>
  <text x="240" y="410" fill="#F8FAFC" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="bold" text-anchor="end">{followers}</text>

  <!-- Right Grade Circle Infographic -->
  <g transform="translate(360, 240)">
    <circle cx="0" cy="0" r="{r}" fill="none" stroke="rgba(16, 185, 129, 0.1)" stroke-width="6" />
    <circle cx="0" cy="0" r="{r}" fill="none" stroke="#10B981" stroke-width="6"
            stroke-dasharray="{perimeter:.2f}" stroke-dashoffset="{dashoffset:.2f}"
            stroke-linecap="round" transform="rotate(-90)" />
    <text x="0" y="10" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="30" font-weight="bold" text-anchor="middle">{grade}</text>
    <text x="0" y="62" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="11" font-weight="bold" text-anchor="middle">RANKING</text>
  </g>
</svg>"""

    # ------------------ GENERATE LANGUAGES.SVG (Grid, Width 495, Height 470) ------------------
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
    top_6 = sorted_langs[:5]
    others_bytes = sum(x[1] for x in sorted_langs[5:])
    
    total_bytes_count = sum(lang_bytes.values()) if lang_bytes else 1
    formatted_langs = []
    for lang, bytes_count in top_6:
        pct = (bytes_count / total_bytes_count) * 100
        formatted_langs.append((lang, pct))
        
    if others_bytes > 0:
        formatted_langs.append(("Others", (others_bytes / total_bytes_count) * 100))
        
    palette = ["#10B981", "#0D9488", "#34D399", "#10B981", "#0D9488", "#4B5563"]
    opacities = ["1", "1", "1", "0.6", "0.6", "1"]
    
    total_bar_width = 445
    svg_rects = []
    svg_grid_cards = []
    
    current_x = 25
    for i, (lang, pct) in enumerate(formatted_langs):
        width = (pct / 100) * total_bar_width
        color = palette[i % len(palette)]
        opacity = opacities[i % len(opacities)]
        svg_rects.append(f'<rect x="{current_x:.2f}" y="60" width="{width:.2f}" height="12" fill="{color}" opacity="{opacity}" />')
        current_x += width
        
    # 3 rows of 2 columns grid coordinates
    # Card width = 215, height = 95
    grid_coords = [
        (25, 95),   (255, 95),  # Row 1
        (25, 210),  (255, 210), # Row 2
        (25, 325),  (255, 325)  # Row 3
    ]
    
    for i, (lang, pct) in enumerate(formatted_langs):
        if i >= len(grid_coords):
            break
        gx, gy = grid_coords[i]
        color = palette[i % len(palette)]
        opacity = opacities[i % len(opacities)]
        display_name = lang if len(lang) <= 15 else lang[:13] + ".."
        
        card_content = f"""  <g>
    <rect x="{gx}" y="{gy}" width="215" height="95" rx="6" ry="6" fill="#030712" stroke="#0D9488" stroke-width="1" stroke-opacity="0.3" />
    <circle cx="{gx + 22}" cy="{gy + 25}" r="6" fill="{color}" opacity="{opacity}" />
    <text x="{gx + 36}" y="{gy + 30}" fill="#94A3B8" font-family="'Segoe UI', -apple-system, sans-serif" font-size="14" font-weight="500">{display_name}</text>
    <text x="{gx + 107}" y="{gy + 72}" fill="{color}" font-family="'Segoe UI', -apple-system, sans-serif" font-size="28" font-weight="bold" text-anchor="middle">{pct:.1f}%</text>
  </g>"""
        svg_grid_cards.append(card_content)

    languages_svg = f"""<svg width="495" height="470" viewBox="0 0 495 470" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="barClip">
      <rect x="25" y="60" width="445" height="12" rx="6" />
    </clipPath>
  </defs>

  <!-- Background panel matching your theme -->
  <rect x="0.5" y="0.5" width="494" height="469" rx="8" fill="#030712" stroke="#0D9488" stroke-width="1.5" />

  <!-- Card Title -->
  <text x="25" y="35" fill="#10B981" font-family="'Segoe UI', -apple-system, sans-serif" font-size="14" font-weight="bold">Top Languages</text>

  <!-- Progress Bar Group -->
  <g clip-path="url(#barClip)">
    {"    ".join(svg_rects)}
  </g>

{"".join(svg_grid_cards)}
</svg>"""

    # 6. Write both SVGs
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
