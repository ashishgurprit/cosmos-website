#!/usr/bin/env python3
"""
Fix blog post layouts by:
1. Changing Layout import to BlogLayout
2. Removing duplicate header navigation
3. Removing duplicate post header/meta (now in BlogLayout)
4. Keeping only the content
"""

import os
import re
from pathlib import Path

BLOG_DIR = Path("src/pages/blog")

def fix_blog_post(file_path):
    """Fix a single blog post file"""
    print(f"Processing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Change Layout import to BlogLayout
    content = content.replace(
        "import Layout from '../../layouts/Layout.astro';",
        "import BlogLayout from '../../layouts/BlogLayout.astro';"
    )

    # Step 2: Extract frontmatter and content
    # Split by --- markers
    parts = content.split('---')
    if len(parts) < 3:
        print(f"  Warning: Unexpected format in {file_path.name}")
        return False

    frontmatter = parts[1]
    after_frontmatter = '---'.join(parts[2:])

    # Step 3: Find where actual content starts (after <div class="post-content">)
    content_start_match = re.search(r'<div class="post-content">\s*', after_frontmatter)
    if not content_start_match:
        print(f"  Warning: Could not find post-content div in {file_path.name}")
        return False

    content_start_pos = content_start_match.end()
    actual_content = after_frontmatter[content_start_pos:]

    # Step 4: Find where content ends (before closing tags)
    # Remove closing </div>, </div>, </article>, </Layout> tags at the end
    actual_content = actual_content.strip()

    # Remove common closing patterns at the end
    closing_patterns = [
        r'\s*</div>\s*</div>\s*</article>\s*</Layout>\s*$',
        r'\s*</div>\s*</article>\s*</Layout>\s*$',
        r'\s*</article>\s*</Layout>\s*$',
        r'\s*</Layout>\s*$'
    ]

    for pattern in closing_patterns:
        actual_content = re.sub(pattern, '', actual_content)

    # Step 5: Reconstruct the file with BlogLayout
    new_content = f"""---
{frontmatter}---

<BlogLayout
  title={{`${{title}} | Cosmos Web Tech Blog`}}
  description={{description}}
  publishedAt={{publishedAt}}
  author={{author}}
  authorTitle={{authorTitle}}
  category={{category}}
  readTime={{readTime}}
  heroImage={{heroImage}}
>
{actual_content}
</BlogLayout>
"""

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✓ Fixed {file_path.name}")
    return True

def main():
    """Process all blog posts"""
    blog_files = list(BLOG_DIR.glob("*.astro"))
    blog_files = [f for f in blog_files if f.name != "index.astro"]

    print(f"Found {len(blog_files)} blog posts to fix\n")

    success_count = 0
    for blog_file in blog_files:
        if fix_blog_post(blog_file):
            success_count += 1

    print(f"\n✓ Successfully fixed {success_count}/{len(blog_files)} blog posts")

if __name__ == "__main__":
    main()
