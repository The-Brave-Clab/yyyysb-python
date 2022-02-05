import datetime
import json
import pathlib
import os
import html

import utils


def ensure_folders(folder : pathlib.Path) -> pathlib.Path:
    if not folder.is_dir():
        os.makedirs(str(folder), exist_ok=True)
    return folder


current_path = ensure_folders(pathlib.Path().absolute() / "downloaded")
downloaded_count = {}

def get_image_filename_from_url(url : str) -> str:
    url_no_query = url.split("?")[0]
    url_filename = url_no_query.split("/")[-1]
    return url_filename.replace(".nop", "")


def download(url : str, target_file : pathlib.Path):
    response = utils.global_session.get(url)
    target_file.write_bytes(response.content)


def save_image_alike(json_item : dict, url_key : str, folder : pathlib.Path):
    for quality in json_item["attributes"][url_key]:
        url = json_item["attributes"][url_key][quality]
        url_filename_ext = get_image_filename_from_url(url).split(".")[-1]
        photo_file = folder / f"{quality}.{url_filename_ext}"
        download(url, photo_file)
    del json_item["attributes"][url_key]


def save_html(title : str, body : str, folder : pathlib.Path):
    img_links = utils.get_img_links(body)
    for img_link in img_links:
        original_link = utils.convert_img_link_to_original(img_link)
        img_filename = get_image_filename_from_url(original_link)
        img_file = folder / img_filename
        download(original_link, img_file)
        body = body.replace(img_link, img_filename)

    html_text = f'<!DOCTYPE html><html><head><title>{title}</title></head><body>{body}</body></html>'
    html_file = folder / "content.html"
    html_file.write_bytes(html_text.encode("utf-8"))


def save_item(json_item : dict):
    folder = current_path / json_item["type"] / json_item["id"]
    if folder.is_dir():
        return

    ensure_folders(folder)

    item_type = json_item["type"]

    if item_type not in downloaded_count:
        downloaded_count[item_type] = 0
    downloaded_count[item_type] += 1

    if item_type == "tlPost":
        text = json_item["attributes"]["text"].encode("utf-8")
        post_file = folder / "text.txt"
        post_file.write_bytes(text)
        del json_item["attributes"]["text"]
    elif item_type in ["photo", "thumbnail"]:
        save_image_alike(json_item, "urls", folder)
    elif item_type == "user":
        save_image_alike(json_item, "avatarUrls", folder)
    elif item_type in ["information", "article", "video"]:
        title = json_item["attributes"]["title"]
        body = json_item["attributes"]["renderedBody"]
        if item_type == "video":
            video_html = json_item["attributes"]["html"]
            embedded_link = utils.get_vimeo_embedded_link_from_html(video_html)
            video_filename = utils.get_vimeo_filename_from_html(video_html)
            video_ref_file = pathlib.PurePosixPath("../../vimeo") / json_item["relationships"]["vimeo"]["data"]["id"] / video_filename
            video_html = video_html.replace(html.escape(embedded_link), html.escape(str(video_ref_file)))
            body = body + video_html

        save_html(title, body, folder)
        del json_item["attributes"]["title"]
        del json_item["attributes"]["renderedBody"]
    elif item_type == "vimeo":
        video_html = json_item["attributes"]["html"]
        embedded_link = utils.get_vimeo_embedded_link_from_html(video_html)
        direct_link = utils.get_vimeo_direct_link_from_embedded_link(embedded_link)
        video_filename = utils.get_vimeo_filename_from_html(video_html)
        video_file = folder / video_filename
        download(direct_link, video_file)
        del json_item["attributes"]["html"]
    elif item_type in ["choice", "poll", "informationCategory"]:
        pass
    else:
        print(json.dumps(json_item, indent=2, ensure_ascii=False))

    data_file = folder / "data.json"
    data_file.write_bytes(json.dumps(json_item, indent=2, ensure_ascii=False).encode("utf-8"))


def save_data(json_obj : dict):
    data = json_obj["data"]
    save_item(data)

    if "included" in json_obj:
        included = json_obj["included"]
        for i in included:
            save_item(i)


def timeline_posts():
    print("Downloading timeline posts...")
    jst_time_delta = datetime.timedelta(hours=9)
    jst_tz = datetime.timezone(jst_time_delta)

    current_time = datetime.datetime.now(jst_tz).isoformat(timespec='milliseconds')

    while True:

        url = f"https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/ids?from={current_time}"

        try:
            posts_response = utils.global_session.get(url)
            posts_json = posts_response.json()
            posts_data = posts_json["data"]
        except:
            print("Failed to retrieve timeline posts")
            return

        if len(posts_data) == 0:
            break

        posts_data = sorted(posts_data, key = lambda post: datetime.datetime.fromisoformat(post["attributes"]["publishedAt"]), reverse=True)
        for post in posts_data:
            post_url = "https://yuyuyu.api.app.c-rayon.com/api/public/tl_posts/{}".format(post["id"])
            try:
                post_response = utils.global_session.get(post_url)
                post_json = post_response.json()
            except: 
                print("Failed to retrieve timeline post {}".format(post["id"]))
                continue

            current_time = datetime.datetime.fromisoformat(post_json["data"]["attributes"]["publishedAt"])
            save_data(post_json)


def informations(per_page : int):
    print("Downloading informations...")
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

        for post_index in range(len(page_data)):
            post_id = page_data[post_index]["id"]

            post_url = f"https://yuyuyu.api.app.c-rayon.com/api/public/informations/{post_id}"

            try:
                post_response = utils.global_session.get(post_url)
                post_json = post_response.json()
            except:
                print(f"Failed to retrieve informations/{post_id} data")
                break
            
            save_data(post_json)

        if len(page_data) < per_page:
            break
        current_page += 1


def private_content(content_type : str, per_page : int, has_post_user : bool = True):
    print(f"Downloading {content_type}...")
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

        for post_index in range(len(page_data)):
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
            except:
                print(f"Failed to retrieve {content_type}/{post_id} data")
                break

            save_data(content_json)

            # content_text = utils.get_text_from_html(content_html)
            # included_data = utils.get_included_content_dict(content_json["included"])
            # if has_post_user:
            #     user_name = [inc for inc in content_json["included"] if inc["type"] == "user"][0]["attributes"]["name"]
            # published_time = content_json["data"]["attributes"]["publishDate"]

        if len(page_data) < per_page:
            break
        current_page += 1


if __name__ == "__main__":
    print("Data Downloader")
    print()

    utils.login()

    timeline_posts()
    informations(20)
    private_content("articles", 6)
    private_content("videos", 6, False)

    print("Total downloaded:")
    for t in downloaded_count:
        print(f"\t{t}: {downloaded_count[t]}")

