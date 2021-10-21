import requests
import datetime

if __name__ == "__main__":
    current_time = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='milliseconds')
    url = f"https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/ids?from={current_time}"

    session = requests.session()

    posts_response = session.get(url)
    posts_json = posts_response.json()
    posts_data = posts_json["data"]

    posts_data = sorted(posts_data, key = lambda post: datetime.datetime.fromisoformat(post["attributes"]["publishedAt"]), reverse=True)
    posts_urls = ["https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/{}".format(post["id"]) for post in posts_data]
    posts_responses = [session.get(url) for url in posts_urls]
    posts_jsons = [response.json() for response in posts_responses]

    for i in range(len(posts_jsons)):
        post_json = posts_jsons[i]
        print("{}. {}...".format(i, post_json["data"]["attributes"]["text"][:40].replace("\n", "\\n")))

    post_index = int(input("Enter the number of the post: "))

    post = posts_jsons[post_index]

    user_name = [inc for inc in post["included"] if inc["type"] == "user"][0]["attributes"]["name"]
    published_time = datetime.datetime.fromisoformat(post["data"]["attributes"]["publishedAt"])
    post_text = post["data"]["attributes"]["text"]
    images = [inc for inc in post["included"] if inc["type"] == "photo"]
    image_urls = [image["attributes"]["urls"]["original"] for image in images]

    print(f"\n\n\nUser:{user_name}")
    print(f"Published At:{published_time}")
    print("\n---------------------------------------\n")
    print(post_text)
    print("\n---------------------------------------\n")
    print("\nImages:")
    for image_url in image_urls:
        print(f"\t{image_url}")
    print("\n")



