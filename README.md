# ゆゆゆ勇者部 Python client

A very simple python client for web application [ゆゆゆ勇者部](https://c-rayon.com/result/yuyuyu/).

## Requirements

You'll need to use Python 3 to run the script.

The script uses the following 3rd party libraries:
 * `requests`
 * `BeautifulSoup4` (Optional)
 * `markdownify` (Optional)
 * `vimeo-downloader` (Optional)

To install the dependencies with pip:

```sh
python -m pip install requests beautifulsoup4 markdownify vimeo-downloader
```

## Usage

Execute the script with Python 3.

```sh
python main.py
```

For the downloader, execute the `download.py` script. The files will be placed in the current working directory, under `downloaded` folder.

```sh
python download.py
```

## Disclaimer

When viewing certain contents, you are required to login with your account of Yushabu App.
While we do not store your login info including your email and password, the said info will 
be passed to Web API in **plaintext**.

If this makes you worried, please avoid using your main account. You can register another 
one with another email and a different password, or you can just use this client without
logging in, but certain contents will not be available.
