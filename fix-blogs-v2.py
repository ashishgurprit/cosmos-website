#!/usr/bin/env python3
"""
Fix Cosmos blog posts - Version 2
Properly format for Astro frontmatter with export
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
today = datetime(2025, 1, 13)
dates = []
days_back = 0

while len(dates) < len(blog_files):
    check_date = today - timedelta(days=days_back)
    if check_date.weekday() == 0 or check_date.weekday() == 3:  # Monday or Thursday
        dates.append(check_date)
    days_back += 1

dates.reverse()
print(f"Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")

# Process each blog file
for i, blog_file in enumerate(blog_files):
    print(f"\nProcessing: {blog_file.name}")

    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract current values (they might be const or frontmatter now)
    title_match = re.search(r'(?:const )?title[:\s=]+"(.*?)"', content)
    desc_match = re.search(r'(?:const )?description[:\s=]+"(.*?)"', content)
    category_match = re.search(r'(?:const )?category[:\s=]+"(.*?)"', content)
    readtime_match = re.search(r'(?:const )?readTime[:\s=]+"(.*?)"', content)

    if not title_match:
        print(f"  ⚠️  Skipping - no title found")
        continue

    title = title_match.group(1)
    description = desc_match.group(1) if desc_match else ""
    category = category_match.group(1) if category_match else "Web Design"
    read_time = readtime_match.group(1) if readtime_match else "5 min read"

    # Clean title
    title_clean = re.sub(r'\s*[-–—]\s*Cosmos Web Tech\s*$', '', title)
    pub_date = dates[i]
    slug = blog_file.stem

    # Create proper Astro frontmatter with export
    frontmatter = f"""---
import Layout from '../../layouts/Layout.astro';

export const frontmatter = {{
  title: "{title_clean}",
  description: "{description}",
  publishedAt: "{pub_date.strftime('%Y-%m-%d')}",
  author: "{AUTHOR}",
  authorTitle: "{AUTHOR_TITLE}",
  category: "{category}",
  readTime: "{read_time}",
  heroImage: "/images/blog/{slug}-hero.jpg",
  contentImage: "/images/blog/{slug}-content.jpg",
  infographic: "/images/blog/{slug}-infographic.jpg"
}};

const {{ title, description, publishedAt, author, authorTitle, category, readTime, heroImage, contentImage, infographic }} = frontmatter;
---"""

    # Find content after the frontmatter section
    parts = content.split('---')
    if len(parts) >= 3:
        # Get everything after the second ---
        rest_content = '---'.join(parts[2:])

        # Build new content
        new_content = frontmatter + '\n' + rest_content

        # Fix Layout title reference
        new_content = re.sub(
            r'<Layout title=\{`\${title} \| Cosmos Web Tech Blog`\}',
            '<Layout title={title}',
            new_content
        )
        new_content = re.sub(
            r'<Layout title=\{title\}',
            '<Layout title={`${title} | Cosmos Web Tech Blog`}',
            new_content
        )

        # Fix date references
        new_content = re.sub(
            r'\{new Date\(frontmatter\.publishedAt\)',
            '{new Date(publishedAt)',
            new_content
        )

        # Fix all frontmatter references to use destructured variables
        new_content = re.sub(r'\{frontmatter\.category\}', '{category}', new_content)
        new_content = re.sub(r'\{frontmatter\.title\}', '{title}', new_content)
        new_content = re.sub(r'\{frontmatter\.description\}', '{description}', new_content)
        new_content = re.sub(r'\{frontmatter\.readTime\}', '{readTime}', new_content)
        new_content = re.sub(r'\{frontmatter\.heroImage\}', '{heroImage}', new_content)

        # Fix image src in quotes
        new_content = re.sub(
            r'src="\{frontmatter\.heroImage\}"',
            'src={heroImage}',
            new_content
        )

        # Write back
        with open(blog_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  ✅ Updated: {title_clean[:50]}...")
        print(f"     Date: {pub_date.strftime('%Y-%m-%d')}")
    else:
        print(f"  ⚠️  Unexpected format")

print("\n✨ All blogs fixed!")
