import os
import re
import urllib.request
import urllib.parse
import time
import random
from config import PROJECT_ROOT, IMAGE_CACHE_DIR


def get_image_urls(query, count=8, exclude_urls=None):
    if exclude_urls is None:
        exclude_urls = set()

    encoded_query = urllib.parse.quote(query)
    urls = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    # 1. Try Google Images
    try:
        url = f"https://www.google.com/search?tbm=isch&q={encoded_query}"
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        matches = re.findall(r'\["(http[^"]+?\.(?:jpg|jpeg|png))"', html)
        for m in matches:
            if m not in exclude_urls and m not in urls:
                urls.append(m)
                if len(urls) >= count:
                    return urls
    except Exception as e:
        print(f"Google search failed for {query}: {e}")

    # 2. Fallback to Bing Images
    if len(urls) < count:
        try:
            url = f"https://www.bing.com/images/search?q={encoded_query}"
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
            matches = re.findall(r'murl&quot;:&quot;(http[^&]+?)&quot;', html)
            for m in matches:
                if m not in exclude_urls and m not in urls:
                    urls.append(m)
                    if len(urls) >= count:
                        return urls
        except Exception as e:
            print(f"Bing search failed for {query}: {e}")

    return urls


def download_image(url, save_path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception:
        return False


def fetch_term_images(word, definition, context, term_id, is_regenerate=False):
    fetched_urls = set()
    selected_urls = []

    queries = [word]

    if definition:
        clean_def = re.sub(r'[^\w\s]', '', definition)
        queries.append(f"{word} {clean_def[:30]}")
    else:
        queries.append(word + " concept")

    if context:
        clean_ctx = re.sub(r'[^\w\s]', '', context)
        queries.append(f"{word} {clean_ctx[:30]}")
    else:
        queries.append(word + " illustration")

    for q in queries:
        urls = get_image_urls(q, count=8, exclude_urls=fetched_urls)
        if urls:
            # If regenerate, pick randomly from pool; otherwise, always pick Top 1
            if is_regenerate:
                chosen_url = random.choice(urls)
            else:
                chosen_url = urls[0]

            selected_urls.append(chosen_url)
            fetched_urls.add(chosen_url)

    if len(selected_urls) < 3:
        more_urls = get_image_urls(word, count=10, exclude_urls=fetched_urls)
        if more_urls:
            if is_regenerate:
                random.shuffle(more_urls)
            needed = 3 - len(selected_urls)
            selected_urls.extend(more_urls[:needed])

    saved_paths = []
    for idx, u in enumerate(selected_urls[:3]):
        ext = "jpg"
        if ".png" in u.lower():
            ext = "png"
        elif ".jpeg" in u.lower():
            ext = "jpeg"

        filename = f"term_{term_id}_{int(time.time())}_{idx}.{ext}"
        save_path = IMAGE_CACHE_DIR / filename

        if download_image(u, str(save_path)):
            try:
                rel_path = os.path.relpath(save_path, PROJECT_ROOT).replace('\\', '/')
            except ValueError:
                rel_path = str(save_path).replace('\\', '/')
            saved_paths.append(rel_path)

    return ",".join(saved_paths)