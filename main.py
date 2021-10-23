import datetime
from getpass import getpass

import requests
from bs4 import BeautifulSoup
from vimeo_downloader import Vimeo

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

def get_bearer_auth() -> BearerAuth:
    if not login_data["loggedIn"]:
        login()

    return BearerAuth(login_data["idToken"])


def get_text_from_html(html : str) -> str:
    soup = BeautifulSoup(html, features="html.parser")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    return soup.get_text(separator="\n")

def get_included_content_dict(included : list) -> dict:
    result = {}
    for inc in included:
        if not inc["type"] in result.keys():
            result[inc["type"]] = []

        result[inc["type"]].append(inc)

    return result

def output_included_content_dict(included_data : dict):
    for kv_pair in included_data.items():

        print(f"{kv_pair[0]}:")

        if kv_pair[0] == "photo" or kv_pair[0] == "thumbnail":
            for include in kv_pair[1]:
                print("\t{}".format(include["attributes"]["urls"]["original"]))
        elif kv_pair[0] == "vimeo":
            for include in kv_pair[1]:
                html = include["attributes"]["html"]
                soup = BeautifulSoup(html, 'html.parser')
                link = soup.find_all('iframe')[0]["src"]
                print(f"\t[Embedded] {link}")
                link_without_params = link.split("?")[0]
                vimeo_video = Vimeo(link_without_params)
                best_stream = vimeo_video.best_stream
                print(f"\t[ Direct ] {best_stream.direct_url}")
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

def timeline_posts():
    jst_time_delta = datetime.timedelta(hours=9)
    jst_tz = datetime.timezone(jst_time_delta)

    current_page = 0
    posts_jsons = []
    current_time = datetime.datetime.now(jst_tz).isoformat(timespec='milliseconds')

    while True:

        url = f"https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/ids?from={current_time}"

        posts_response = global_session.get(url)
        posts_json = posts_response.json()
        posts_data = posts_json["data"]

        posts_data = sorted(posts_data, key = lambda post: datetime.datetime.fromisoformat(post["attributes"]["publishedAt"]), reverse=True)
        posts_urls = ["https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/{}".format(post["id"]) for post in posts_data]
        posts_responses = [global_session.get(url) for url in posts_urls]
        posts_jsons = [response.json() for response in posts_responses]
        
        first_page = current_page == 0
        last_page = len(posts_jsons) < 10 # TODO: 10 is a magic number for now

        for i in range(len(posts_jsons)):
            post_json = posts_jsons[i]
            print("{}. {}...".format(i, post_json["data"]["attributes"]["text"][:40].replace("\n", "")))

        if not first_page:
            print("-. Previous Page")

        if not last_page:
            print("+. Next Page")

        print("q. Back\n")

        action = input("Enter your action: ")
        print()

        if action == "-":
            current_page -= 1
            if current_page == 0:
                current_time = datetime.datetime.now(jst_tz).isoformat(timespec='milliseconds')
            else:
                current_time = posts_jsons[-1]["data"]["attributes"]["publishedAt"]
            print()
            continue

        if action == "+":
            current_page += 1
            if current_page == 0:
                current_time = datetime.datetime.now(jst_tz).isoformat(timespec='milliseconds')
            else:
                current_time = posts_jsons[-1]["data"]["attributes"]["publishedAt"]
            print()
            continue

        if action == "q":
            print()
            break

        post_index = int(action)

        post = posts_jsons[post_index]

        user_name = [inc for inc in post["included"] if inc["type"] == "user"][0]["attributes"]["name"]
        published_time = datetime.datetime.fromisoformat(post["data"]["attributes"]["publishedAt"])
        post_text = post["data"]["attributes"]["text"]
        included_data = get_included_content_dict(post["included"])


        print(f"\n\n\nUser:{user_name}")
        print(f"Published At: {published_time}")
        print("\n---------------------------------------\n")
        print(post_text)
        print("\n---------------------------------------\n")

        output_included_content_dict(included_data)

        input("Press Enter to Go Back...")

        print("\n")

def private_content(content_type : str, per_page : int, has_post_user : bool = True):
    url = f"https://yuyuyu.api.app.c-rayon.com/api/public/{content_type}/latest"
    
    current_page = 1

    while True:
        pagination_url = f"{url}?page={current_page}&per_page={per_page}"

        page_response = global_session.get(pagination_url)
        page_json = page_response.json()
        page_data = page_json["data"]

        first_page = current_page == 1
        last_page = len(page_data) < per_page

        for i in range(len(page_data)):
            title = page_data[i]["attributes"]["title"]
            print(f"{i}. {title}")

        if not first_page:
            print("-. Previous Page")

        if not last_page:
            print("+. Next Page")

        print("q. Back\n")

        action = input("Enter your action: ")
        print()

        if action == "-":
            current_page -= 1
            print()
            continue

        if action == "+":
            current_page += 1
            print()
            continue

        if action == "q":
            print()
            break

        post_index = int(action)
        post_id = page_data[post_index]["id"]

        content_location_url = f"https://yuyuyu.api.app.c-rayon.com/api/private/{content_type}/{post_id}/content_location"

        content_location_response = global_session.get(content_location_url, auth=get_bearer_auth())
        content_location_json = content_location_response.json()
        content_url = content_location_json["data"]["meta"]["content_url"]

        content_response = global_session.get(content_url)
        content_json = content_response.json()
        content_html = content_json["data"]["attributes"]["renderedBody"]

        content_text = get_text_from_html(content_html)
        included_data = get_included_content_dict(content_json["included"])
        if has_post_user:
            user_name = [inc for inc in content_json["included"] if inc["type"] == "user"][0]["attributes"]["name"]
        published_time = content_json["data"]["attributes"]["publishDate"]

        print("\n\n")
        if (has_post_user):
            print(f"User: {user_name}")
        print(f"Published At: {published_time}")
        print("\n---------------------------------------\n")
        print(content_text)
        print("\n---------------------------------------\n")

        output_included_content_dict(included_data)

        input("Press Enter to Go Back...")

        print("\n")

def informations(per_page : int):
    url = "https://yuyuyu.api.app.c-rayon.com/api/public/informations"

    current_page = 1

    while True:
        pagination_url = f"{url}?page={current_page}&per_page={per_page}"

        page_response = global_session.get(pagination_url)
        page_json = page_response.json()
        page_data = page_json["data"]

        first_page = current_page == 1
        last_page = len(page_data) < per_page

        for i in range(len(page_data)):
            title = page_data[i]["attributes"]["title"]
            print(f"{i}. {title}")

        if not first_page:
            print("-. Previous Page")

        if not last_page:
            print("+. Next Page")

        print("q. Back\n")

        action = input("Enter your action: ")
        print()

        if action == "-":
            current_page -= 1
            print()
            continue

        if action == "+":
            current_page += 1
            print()
            continue

        if action == "q":
            print()
            break

        post_index = int(action)
        post_id = page_data[post_index]["id"]

        post_url = f"https://yuyuyu.api.app.c-rayon.com/api/public/informations/{post_id}"
        post_response = global_session.get(post_url)
        post_json = post_response.json()
        
        post_html = post_json["data"]["attributes"]["renderedBody"]
        post_text = get_text_from_html(post_html)
        post_date = post_json["data"]["attributes"]["announcedDate"]
        included_data = get_included_content_dict(post_json["included"])

        print(f"\n\n\nPublished At: {post_date}")
        print("\n---------------------------------------\n")
        print(post_text)
        print("\n---------------------------------------\n")

        output_included_content_dict(included_data)

        input("Press Enter to Go Back...")

        print("\n")

if __name__ == "__main__":
    while True:
        print("\n\n")
        print("0. View Timeline Posts")
        print("1. View Informations")
        print("2. View Articles (REQUIRES LOGIN)")
        print("3. View Videos (REQUIRES LOGIN)")
        print("q. Exit\n")

        action = input("Enter your action: ")

        if action == "q":
            break

        print()
        print()

        if action == "0":
            timeline_posts()
        elif action == "1":
            informations(20)
        elif action == "2":
            private_content("articles", 6)
        elif action == "3":
            private_content("videos", 6, False)
