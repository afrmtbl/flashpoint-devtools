# flashpoint-devtools

![Screenshot of the program](https://github.com/afrmtbl/flashpoint-devtools/blob/master/screenshot.png)

## Installation and Usage

#### If Python 3 is not installed

1. Download the latest release
2. Extract the zip
3. Double click the `FlashpointDevTools` shortcut or the executable located at `devtools/FlashpointDevTools.exe` to launch

#### If Python 3 is installed

```bash
git clone https://github.com/afrmtbl/flashpoint-devtools
pip install requests
cd flashpoint-devtools
python devtools.py
```
`requests` isn't actually required yet, but most likely will be in the future

## Building
Note: will only build for current platform
```bash
pip install pyinstaller
pyinstaller devtools.spec
```
