#!/usr/bin/env python3
"""
Properly fix blog posts by removing:
1. Duplicate footers
2. Closing </Layout> tags
3. Style sections
And keeping only the actual blog content.
"""

import os
import re
from pathlib import Path

BLOG_DIR = Path("src/pages/blog")

def fix_blog_post(file_path):
    """Fix a single blog post file by removing unwanted sections"""
    print(f"Processing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by frontmatter markers
    parts = content.split('---')
    if len(parts) < 3:
        print(f"  Warning: Unexpected format in {file_path.name}")
        return False

    frontmatter = parts[1]
    after_frontmatter = '---'.join(parts[2:])

    # Find where BlogLayout starts
    blog_layout_match = re.search(r'<BlogLayout[^>]*>\s*', after_frontmatter)
    if not blog_layout_match:
        print(f"  Warning: Could not find BlogLayout in {file_path.name}")
        return False

    content_start_pos = blog_layout_match.end()
    remaining_content = after_frontmatter[content_start_pos:]

    # Remove everything after (and including) the first <footer> tag
    footer_match = re.search(r'<footer\s+class="post-footer"[^>]*>',  remaining_content)
    if footer_match:
        actual_content = remaining_content[:footer_match.start()].strip()
    else:
        # Try to find </Layout> closing tag
        layout_close_match = re.search(r'</Layout>', remaining_content)
        if layout_close_match:
            actual_content = remaining_content[:layout_close_match.start()].strip()
        else:
            # Try to find <style> tag
            style_match = re.search(r'<style>', remaining_content)
            if style_match:
                actual_content = remaining_content[:style_match.start()].strip()
            else:
                # Try to find </BlogLayout>
                blog_layout_close_match = re.search(r'</BlogLayout>', remaining_content)
                if blog_layout_close_match:
                    actual_content = remaining_content[:blog_layout_close_match.start()].strip()
                else:
                    actual_content = remaining_content.strip()

    # Extract BlogLayout props from original
    blog_layout_opening = after_frontmatter[blog_layout_match.start():blog_layout_match.end()]

    # Reconstruct the file
    new_content = f"""---
{frontmatter}---

{blog_layout_opening}
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
