#!/usr/bin/env python3
"""
Fix Cosmos blog posts:
1. Convert to frontmatter format
2. Assign predated publication dates (2 blogs/week)
3. Fix title duplication
4. Set up proper image paths
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

BLOG_DIR = Path("src/pages/blog")
AUTHOR = "Ashish Ganda"
AUTHOR_TITLE = "Founder, Cosmos Web Tech"

# Get all blog files (exclude index.astro)
blog_files = sorted([
    f for f in BLOG_DIR.glob("*.astro")
    if f.name != "index.astro"
])

print(f"Found {len(blog_files)} blog files")

# Calculate publication dates (2 per week, going backwards from today)
# Publishing on Monday and Thursday
today = datetime(2025, 1, 13)  # Today's actual date (2025)
dates = []

current_date = today
days_back = 0

# We need dates for 27 blogs, 2 per week
while len(dates) < len(blog_files):
    # Start from today and go backwards
    check_date = today - timedelta(days=days_back)

    # Publish on Mondays (0) and Thursdays (3)
    if check_date.weekday() == 0 or check_date.weekday() == 3:
        dates.append(check_date)

    days_back += 1

# Reverse so oldest is first
dates.reverse()

print(f"Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")

# Process each blog file
for i, blog_file in enumerate(blog_files):
    print(f"\nProcessing: {blog_file.name}")

    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract current constants
    title_match = re.search(r'const title = "(.*?)";', content)
    desc_match = re.search(r'const description = "(.*?)";', content)
    category_match = re.search(r'const category = "(.*?)";', content)
    readtime_match = re.search(r'const readTime = "(.*?)";', content)

    if not title_match:
        print(f"  ⚠️  Skipping - no title found")
        continue

    title = title_match.group(1)
    description = desc_match.group(1) if desc_match else ""
    category = category_match.group(1) if category_match else "Web Design"
    read_time = readtime_match.group(1) if readtime_match else "5 min read"

    # Remove " - Cosmos Web Tech" or similar from title if present
    title_clean = re.sub(r'\s*[-–—]\s*Cosmos Web Tech\s*$', '', title)

    # Assign publication date
    pub_date = dates[i]

    # Create slug from filename
    slug = blog_file.stem

    # Create frontmatter
    frontmatter = f"""---
title: "{title_clean}"
description: "{description}"
publishedAt: "{pub_date.strftime('%Y-%m-%d')}"
author: "{AUTHOR}"
authorTitle: "{AUTHOR_TITLE}"
category: "{category}"
readTime: "{read_time}"
heroImage: "/images/blog/{slug}-hero.jpg"
contentImage: "/images/blog/{slug}-content.jpg"
infographic: "/images/blog/{slug}-infographic.jpg"
---"""

    # Replace the old frontmatter section (between first --- and next ---)
    # The current format has:
    # ---
    # import Layout...
    # const title = ...
    # ---

    # Find the frontmatter section
    parts = content.split('---', 2)
    if len(parts) >= 3:
        # Keep import statement
        import_section = parts[1].strip()
        # Extract import line
        import_match = re.search(r"import Layout.*?;", import_section)
        import_line = import_match.group(0) if import_match else "import Layout from '../../layouts/Layout.astro';"

        # Rest of content after frontmatter
        rest_content = parts[2]

        # Build new content
        new_content = f"""---
{import_line}
{frontmatter[3:]}

{rest_content}"""

        # Fix the Layout title tag - remove duplication
        new_content = re.sub(
            r'<Layout title=\{`\${title} \| Cosmos Web Tech Blog`\}',
            '<Layout title={title}',
            new_content
        )

        # Replace date formatting to use frontmatter
        new_content = re.sub(
            r'\{new Date\(date\)\.toLocaleDateString',
            '{new Date(frontmatter.publishedAt).toLocaleDateString',
            new_content
        )

        # Replace {title} with {frontmatter.title}
        new_content = re.sub(
            r'(<h1>\{)(title)(\}</h1>)',
            r'\1frontmatter.\2\3',
            new_content
        )

        # Replace {description} with {frontmatter.description}
        new_content = re.sub(
            r'(<p class="post-excerpt">\{)(description)(\}</p>)',
            r'\1frontmatter.\2\3',
            new_content
        )

        # Replace {category} with {frontmatter.category}
        new_content = re.sub(
            r'(<span class="post-category">\{)(category)(\}</span>)',
            r'\1frontmatter.\2\3',
            new_content
        )

        # Replace {readTime} with {frontmatter.readTime}
        new_content = re.sub(
            r'(<span class="read-time">\{)(readTime)(\}</span>)',
            r'\1frontmatter.\2\3',
            new_content
        )

        # Update hero image reference
        new_content = re.sub(
            r'<img src="/images/blog/[^"]*-1\.jpg"',
            f'<img src="{{frontmatter.heroImage}}"',
            new_content
        )

        # Write back
        with open(blog_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  ✅ Updated: {title_clean[:50]}...")
        print(f"     Date: {pub_date.strftime('%Y-%m-%d')}")
    else:
        print(f"  ⚠️  Unexpected format")

print("\n✨ All blogs updated!")
print("\nNext steps:")
print("1. Create hero images for each blog (dimensions: 1200x630)")
print("2. Create content images for each blog (dimensions: 800x450)")
print("3. Create infographics for each blog (dimensions: 800x1200)")
