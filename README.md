# koala-upb-scraper.py

Python3 script to download the current term's material from https://koala.uni-paderborn.de

## Usage

Clone the repository and install the dependencies:

```shell
$ pip3 install requests beautifulsoup4 PyYaml
```

Create `prefs.yaml` in the root and enter your credentials:

```yaml
username: replace_me
base64password: your_password_in_base64
```

Then you can run the script and it will scrape everything automatically.
You can rerun the script as often as you like, files are timestamped and only newer versions of a file will be downloaded.
