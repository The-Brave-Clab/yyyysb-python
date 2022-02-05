import datetime
from getpass import getpass

import requests

use_beautiful_soup = True

try:
    from bs4 import BeautifulSoup
except:
    use_beautiful_soup = False

use_vimeo_downloader = True

try:
    from vimeo_downloader import Vimeo
except:
    use_vimeo_downloader = False

use_markdownify = True

try:
    from markdownify import markdownify as md
except:
    use_markdownify = False

global_session = requests.session()
login_data = {"loggedIn": False}

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

def print_login_message():
    print("The current action requires you to login your account of the Yushabu App")

    print("\n+----------------------------------------+")
    print("|                                        |")
    print("|                WARNING!                |")
    print("|                                        |")
    print("+----------------------------------------+\n")

    print("We do not store your email and password. However, your login info will be passed to the App in PLAINTEXT!")
    print("The only thing stored is the token of your account after you have logged in.")
    print("If you are concerned, please avoid using your frequently used email and password. Register a new one, or just leave.")
    print("You only need to login once while using this client. Your password is hidden during input.")
    print("\n\n")

def login():
    print_login_message()

    try:
        email = input("Email: ")
        password = getpass("Password: ")

        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = global_session.post("https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyCvopRLMWoEp8l_QoggkujiYLq2WyHX77k", data=payload)

        if response.status_code != 200:
            print("Login failed!")
            return

        user_info = response.json()
        print("Logged in as {}.".format(user_info["displayName"]))

        login_data["loggedIn"] = True
        login_data["localId"] = user_info["localId"]
        login_data["idToken"] = user_info["idToken"]
        login_data["refreshToken"] = user_info["refreshToken"]
    except:
        print("Login failed!")
        login_data["loggedIn"] = False

def get_bearer_auth() -> BearerAuth:
    if not login_data["loggedIn"]:
        login()

    return BearerAuth(login_data["idToken"])


def convert_img_link_to_original(link : str) -> str:
    link_split = link.split("?")
    link_no_param_split = link_split[0].split(".")
    suffix = link_no_param_split[-2] + "." + link_no_param_split[-1]
    return link.replace(suffix, "nop")


def get_img_links(html : str) -> list:
    img_links = []

    if use_beautiful_soup:
        soup = BeautifulSoup(html, features="html.parser")
        for img in soup.findAll('img'):
            link = img.get('src')
            img_links.append(link)
    else:
        start = 0
        end = 0
        while True:
            start = html.find('<img src=', end)
            if start == -1:
                break
            end = html.find('>', start)
            if end == -1:
                break

            link = html[start:end].split('"')[1]
            img_links.append(link)

    return img_links

def process_img_link(html : str, img_links : list) -> str:    
    for link in img_links:
        html = html.replace(link, convert_img_link_to_original(link))

    return html


def get_text_from_html(html : str) -> str:
    try:
        img_links = get_img_links(html)
        html = process_img_link(html, img_links)

        if use_markdownify:
            return md(html).replace("\n\n", "\n")
        elif use_beautiful_soup:
            soup = BeautifulSoup(html, features="html.parser")
            # kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()    # rip it out

            # get text
            return soup.prettify()
        else:
            return html
    except:
        return html


def get_included_content_dict(included : list) -> dict:
    result = {}
    for inc in included:
        if not inc["type"] in result.keys():
            result[inc["type"]] = []

        result[inc["type"]].append(inc)

    return result

def get_vimeo_filename_from_html(html : str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('iframe')[0]["title"]

def get_vimeo_embedded_link_from_html(html : str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('iframe')[0]["src"]

def get_vimeo_direct_link_from_embedded_link(link : str) -> str:
    link_without_params = link.split("?")[0]
    vimeo_video = Vimeo(link_without_params)
    return vimeo_video.best_stream.direct_url

def output_included_content_dict(included_data : dict):
    for kv_pair in included_data.items():

        print(f"{kv_pair[0]}:")

        if kv_pair[0] == "photo" or kv_pair[0] == "thumbnail":
            for include in kv_pair[1]:
                print("\t{}".format(include["attributes"]["urls"]["original"]))
        elif kv_pair[0] == "vimeo":
            for include in kv_pair[1]:
                try:
                    html = include["attributes"]["html"]
                    link = get_vimeo_embedded_link_from_html(html)
                    print(f"\t[Embedded] {link}")
                except:
                    print("\tFailed to get the embedded link of vimeo video")
                    continue
                if use_vimeo_downloader:
                    try:
                        best_stream_url = get_vimeo_direct_link_from_embedded_link(link)
                        print(f"\t[ Direct ] {best_stream_url}")
                    except:
                        print("\tFailed to get the direct link of vimeo video")
                        continue
        elif kv_pair[0] == "user":
            for include in kv_pair[1]:
                print("\t{}".format(include["attributes"]["name"]))
                print("\t{}".format(include["attributes"]["avatarUrls"]["original"]))
        elif kv_pair[0] == "informationCategory":
            for include in kv_pair[1]:
                print("\t{}".format(include["attributes"]["name"]))
        else:
            for include in kv_pair[1]:
                print("\t(Unsupported) {}".format(include["id"]))
                
        print()