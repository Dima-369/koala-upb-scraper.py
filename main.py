# -*- coding: utf-8 -*-

import base64
import json
import os
import re
import shutil
import sys
import threading
import time

import requests
import yaml
from bs4 import BeautifulSoup

modifiedList = dict()
prefs_file = "prefs.yaml"


def download_inv(curr_dir, start_id, req):
    global modifiedList

    s = req.post('https://koala.uni-paderborn.de/desktop/explorer/data',
                 headers={'X-Requested-With': 'XMLHttpRequest'},
                 data=json.dumps({'command': 'inventoryData',
                                  'id': start_id}))
    if 'Sie haben nicht die erforderlichen Rechte, ' \
       'um diese Aktion durchzuführen.' in s.text:
        print("inventoryData blocked on id: {id}!".format(id=start_id))
        return

    data = json.loads(s.text)
    for i in range(len(data["inventoryData"])):
        if curr_dir + data["inventoryData"][i]["name"] in modifiedList:
            if str(modifiedList[curr_dir + data["inventoryData"][i][
                "name"]]) == \
                    str(data["inventoryData"][i]["lastChangedDate"]):
                continue

        if data["inventoryData"][i]["type"] == "container":
            new_dir = '{}{}/'.format(curr_dir,
                                     data["inventoryData"][i]["name"])
            print(
                '{} ---- {}'.format(data["inventoryData"][i]["name"],
                                    new_dir))
            if not os.path.exists("koala/" + new_dir):
                os.makedirs("koala/" + new_dir)
            download_inv(new_dir, data["inventoryData"][i]["id"], req)

        elif data["inventoryData"][i]["type"] == "document":
            url = 'https://koala.uni-paderborn.de/download/{}/{}' \
                .format(data["inventoryData"][i]["id"],
                        data["inventoryData"][i]["name"])
            s = req.get(url, stream=True)
            print("\t" + curr_dir + data["inventoryData"][i]["name"])
            with open("koala/{}{}".format(
                    curr_dir, data["inventoryData"][i]["name"]), 'wb') as f:
                shutil.copyfileobj(s.raw, f)
            del s

        modifiedList[curr_dir + data["inventoryData"][i]["name"]] = \
            data["inventoryData"][i]["lastChangedDate"]


def work_module(r, module_url, module_name):
    if not os.path.exists("koala/" + module_name):
        os.makedirs("koala/" + module_name)

    session = r.get(module_url,
                    headers={'X-Requested-With': 'XMLHttpRequest'})

    if session.text.startswith('<!DOCTYPE HTML>'):
        print('TODO: Module: {} does not have any content!'
              .format(module_name))
        return

    soup = BeautifulSoup(session.text, "html.parser")
    links2 = soup.find_all('a')
    for index2, link2 in enumerate(links2):
        if len(link2.contents) > 0:
            folder = str(link2.contents[0]).replace('<strong>', '').replace(
                '</strong>', '')
            folder_url = link2.get('href')

            link_id = re.findall(r'(?<=units/)[^/]*', folder_url)[0]

            print('{} - {}: {}'.format(folder, link_id, folder_url))

            new_dir = '{}/{}'.format(module_name, folder)
            if not os.path.exists("koala/" + new_dir):
                os.makedirs("koala/" + new_dir)

            download_inv("{}/{}/".format(module_name, folder), link_id, r)


def fetch_parallel(r, urls, names):
    threads = []

    for url, name in zip(urls, names):
        threads.append(
            threading.Thread(target=work_module, args=(r, url, name)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()


def scrape(payload):
    """Login with the user credentials, verify the login and start scraping."""
    r = requests.Session()

    try:
        session = r.get('https://koala.uni-paderborn.de/signin/')
    except requests.ConnectionError:
        print("Can't retrieve Koala's login page!")
        sys.exit(1)

    payload["csrf_token"] = \
        re.findall(r'(?<=csrf_token" value=")[^"]*', session.text)[0]

    try:
        session = r.post('https://koala.uni-paderborn.de/signin/',
                         data=payload)
    except requests.ConnectionError:
        print("Can't login into Koala!")
        sys.exit(3)

    if 'Postfach' not in session.text:
        print('Are your credentials correct?')
        sys.exit(1)

    initiate_module_scraping(r, session.text)


def initiate_module_scraping(r, html_text):
    """Parses all module links from the passed HTML text to start scraping."""
    soupy = BeautifulSoup(html_text, "html.parser")
    module_urls = []
    module_names = []
    links = soupy.find_all('a')
    for index, link in enumerate(links):
        if len(link.contents) > 0:
            if link.get('href').endswith('/units/'):
                module_urls.append(link.get('href'))
                module_names.append(
                    links[index - 1].contents[0].replace('/', '-'))

    fetch_parallel(r, module_urls, module_names)


def update_last_modified_file():
    """Update lastModified.txt with the global lastModified list."""
    with open('lastModified.txt', 'w', encoding='utf-8') as f:
        for module in modifiedList:
            f.write('{}²{}\n'.format(module, str(modifiedList[module])))


def parse_last_modified():
    """Parse lastModified.txt into the global variable to remember downloads.

    We also use the file in cases where the document gets updated the server
    to download a fresh copy.
    """
    if os.path.exists('lastModified.txt'):
        with open('lastModified.txt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                elements = line.split('²')
                if len(elements) == 2:
                    modifiedList[elements[0]] = elements[1]
                else:
                    modifiedList[elements[0]] = 0
    else:
        open('lastModified.txt', 'w+', encoding='utf-8')


def generate_payload_from_credentials():
    """Return the username and password from credentials.txt as a dictionary."""
    if os.path.exists(prefs_file):
        with open(prefs_file, encoding='utf-8') as f:
            y = yaml.load(f.read())
            username = y["username"]
            password = base64.b64decode(y["base64password"])
    else:
        print('Create "{file}" and fill it with your information to login:\n\n'
              'username: replace_me\n'
              'base64password: your_password_in_base64'.format(file=prefs_file))
        sys.exit(2)

    return {'values[login]': username, 'values[password]': password}


def remove_empty_folders():
    def process_folder(path):
        """Recursively remove all empty folders in the passed path.

        We start from the containing directory of this script.
        """
        files = os.listdir(path)
        if len(files):
            for fi in files:
                full_path = os.path.join(path, fi)
                if os.path.isdir(full_path):
                    process_folder(full_path)

        files = os.listdir(path)
        if len(files) == 0:
            print("- {}".format(path))
            os.rmdir(path)

    print("\nRemoving empty folders:")
    process_folder("{}/koala/".format(
        os.path.dirname(os.path.realpath(__file__))))


if __name__ == "__main__":
    start = time.time()

    user = generate_payload_from_credentials()
    parse_last_modified()
    scrape(user)
    update_last_modified_file()
    remove_empty_folders()

    print("\nElapsed time: {0:.3g}s".format(time.time() - start))
