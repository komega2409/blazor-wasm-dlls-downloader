import json, requests, argparse, os, re, art
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# download all the dlls
def download_dlls(dlls_filename, base_url, output_dir, proxy):
    create_output_dir(output_dir)
    print('[-] Downloading...')
    for dll in dlls_filename:
        res = requests.get(base_url + "_framework/" + dll, proxies=proxy)
        with open(f'./{output_dir}/{dll}', 'wb+') as downloaded_file:
            downloaded_file.write(res.content)
    print('[+] Done!!!')

# prepare things for downloading
def pre_download(base_url, proxy, exclude_patterns):
    res = requests.get(base_url, proxies=proxy)
    html_content = res.text
    soup = BeautifulSoup(html_content, 'html.parser')
    base_path = get_base_path(soup)
    # webassembly url for download, 
    webassembly_url = get_webassembly_url(base_url, base_path)
    bootfile_url = get_boot_file(webassembly_url, base_path)
    dlls_filename = get_dlls_filename(bootfile_url, exclude_patterns, proxy)
    return webassembly_url, dlls_filename

# get dlls_filename from boot file
def get_dlls_filename(boot_url, exclude_patterns, proxy):
    res = requests.get(boot_url, proxies=proxy)
    json_data = res.json()
    data = json_data['resources']['assembly']
    # 'dotnet.6.0.5.6zo8o7l6qt.js','dotnet.wasm','icudt_CJK.dat','icudt_EFIGS.dat','icudt_no_CJK.dat','icudt.dat'
    dlls_filename = []
    for key in data.keys():
        if not is_excluded(key, exclude_patterns):
            dlls_filename.append(key)
    return dlls_filename

# check is exclided
def is_excluded(filename, exclude_patterns):
    return any(re.search(pattern, filename) for pattern in exclude_patterns)

# get the base path through tag <base> in WebAssembly index.html
def get_base_path(soup):
    base_tag = soup.find('base')
    try:
        if base_tag and 'href' in base_tag.attrs:
            base_href = base_tag['href']
            return base_href
    except:
        return "<base> tag not found!"

# get blazor.boot.json file
def get_boot_file(base_url, base_path):
    BOOT_FILENAME = "_framework/blazor.boot.json"
    parsed_url = urlparse(base_url)
    bootfile_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}" + BOOT_FILENAME
    return bootfile_url

# get base webassembly url from target url
def get_webassembly_url(base_url, base_path):
    parsed_url = urlparse(base_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}"

# create output directory if not exist
def create_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

# check url is valid
def is_valid_url(url):
    url_pattern = re.compile(r'https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)')
    return bool(url_pattern.match(url))

def main():
    # DLLs Downloader
    art.tprint('DLLs Downloader')

    # argparse
    parser = argparse.ArgumentParser("Blazor WASM DDLs Downloader")
    parser.add_argument("-u", "--url", required=True, help="URL of the Blazor WebAssembly app")
    parser.add_argument("-o", "--output-dir", default="downloaded_dlls", help="Directory to save the downloaded DLLs")
    parser.add_argument("-p", '--proxy', help="Proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("-ex", '--exclude', action='store_true', help="Use for exclude Microsoft, System files")

    # parse args
    args = parser.parse_args()
    url = args.url
    output_dir = args.output_dir
    proxy = {'http': args.proxy} if args.proxy else None
    exclude_patterns = [r"Microsoft", r"System"] if args.exclude else []
    
    # check if provided url is valid
    if not is_valid_url(url):
        print("[!] URL is not valid.")
        return
    # do core functions
    webassembly_url, dlls_filename = pre_download(url, proxy, exclude_patterns)
    download_dlls(dlls_filename, webassembly_url, output_dir, proxy)

if __name__  == '__main__':
    main()