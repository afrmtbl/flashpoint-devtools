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

## Building
Note: will only build for current platform
```bash
pip install pyinstaller
pyinstaller devtools.spec
```
