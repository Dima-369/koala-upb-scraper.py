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
You can rerun the script as often as you like, files are timestamped by the server and only newer versions of a file will be downloaded.

The downloads are stored in `koala/` with empty subdirectories removed after the script is done downloading.
`lastModified.txt` should have content after it is done and should look like this:

```json
Grundlagen der Computergrafik/Vorlesungsfolien/04-ProjectionD.pdf²1479909553
Einführung in Kryptographie/Vorlesungsfolien/09.pdf²1481736300
Stochastik für Informatiker und Lehramtsstudierende (Übung)/Übungsblatt/Uebungsblatt09hinweise.pdf²1482342429
Grundlagen der Computergrafik/Heimübung - Abgabe/sheets²1479837542
Stochastik für Informatiker und Lehramtsstudierende (Übung)/Übungsblatt/Uebungsblatt10.pdf²1484289727
...
```

## Notes

* It is preferable to run the script twice; sometimes it does not pick up on each subdirectory for some reason
* Videos are usually not downloaded because they are stored differently in the koaLa platform
