import datetime
from getpass import getpass

import utils

def timeline_posts():
    jst_time_delta = datetime.timedelta(hours=9)
    jst_tz = datetime.timezone(jst_time_delta)

    current_page = 0
    posts_jsons = []
    current_time = datetime.datetime.now(jst_tz).isoformat(timespec='milliseconds')

    while True:

        url = f"https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/ids?from={current_time}"

        try:
            posts_response = utils.global_session.get(url)
            posts_json = posts_response.json()
            posts_data = posts_json["data"]
        except:
            print("Failed to retrieve timeline posts")
            break

        posts_data = sorted(posts_data, key = lambda post: datetime.datetime.fromisoformat(post["attributes"]["publishedAt"]), reverse=True)
        posts_urls = ["https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/{}".format(post["id"]) for post in posts_data]
        try:
            posts_responses = [utils.global_session.get(url) for url in posts_urls]
            posts_jsons = [response.json() for response in posts_responses]
        except:
            print("Failed to retrieve timeline posts")
            break
        
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

        try:
            action_int = int(action)
        except:
            continue

        if action_int < 0 or action_int >= len(posts_jsons):
            continue

        post_index = int(action)

        post = posts_jsons[post_index]

        user_name = [inc for inc in post["included"] if inc["type"] == "user"][0]["attributes"]["name"]
        published_time = datetime.datetime.fromisoformat(post["data"]["attributes"]["publishedAt"])
        post_text = post["data"]["attributes"]["text"]
        included_data = utils.get_included_content_dict(post["included"])


        print(f"\n\n\nUser:{user_name}")
        print(f"Published At: {published_time}")
        print("\n---------------------------------------\n")
        print(post_text)
        print("\n---------------------------------------\n")

        utils.output_included_content_dict(included_data)

        input("Press Enter to Go Back...")

        print("\n")

def private_content(content_type : str, per_page : int, has_post_user : bool = True):
    url = f"https://yuyuyu.api.app.c-rayon.com/api/public/{content_type}/latest"
    
    current_page = 1

    while True:
        pagination_url = f"{url}?page={current_page}&per_page={per_page}"

        try:
            page_response = utils.global_session.get(pagination_url)
            page_json = page_response.json()
            page_data = page_json["data"]
        except:
            print(f"Failed to retrieve {content_type} data")
            break

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

        try:
            action_int = int(action)
        except:
            continue

        if action_int < 0 or action_int >= len(page_data):
            continue

        post_index = int(action)
        post_id = page_data[post_index]["id"]

        content_location_url = f"https://yuyuyu.api.app.c-rayon.com/api/private/{content_type}/{post_id}/content_location"

        try:
            content_location_response = utils.global_session.get(content_location_url, auth=utils.get_bearer_auth())
            content_location_json = content_location_response.json()
            content_url = content_location_json["data"]["meta"]["content_url"]
        except:
            print(f"Failed to retrieve {content_type}/{post_id} location data")
            break

        try:
            content_response = utils.global_session.get(content_url)
            content_json = content_response.json()
            content_html = content_json["data"]["attributes"]["renderedBody"]
        except:
            print(f"Failed to retrieve {content_type}/{post_id} data")
            break

        content_text = utils.get_text_from_html(content_html)
        included_data = utils.get_included_content_dict(content_json["included"])
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

        utils.output_included_content_dict(included_data)

        input("Press Enter to Go Back...")

        print("\n")

def informations(per_page : int):
    url = "https://yuyuyu.api.app.c-rayon.com/api/public/informations"

    current_page = 1

    while True:
        pagination_url = f"{url}?page={current_page}&per_page={per_page}"

        try:
            page_response = utils.global_session.get(pagination_url)
            page_json = page_response.json()
            page_data = page_json["data"]
        except:
            print("Failed to retrieve informations data")
            break

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

        try:
            post_response = utils.global_session.get(post_url)
            post_json = post_response.json()
        except:
            print(f"Failed to retrieve informations/{post_id} data")
            break
        
        post_html = post_json["data"]["attributes"]["renderedBody"]
        post_text = utils.get_text_from_html(post_html)
        post_date = post_json["data"]["attributes"]["announcedDate"]
        included_data = utils.get_included_content_dict(post_json["included"])

        print(f"\n\n\nPublished At: {post_date}")
        print("\n---------------------------------------\n")
        print(post_text)
        print("\n---------------------------------------\n")

        utils.output_included_content_dict(included_data)

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
