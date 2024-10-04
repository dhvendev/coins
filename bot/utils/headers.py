import random
from enum import Enum

class DeviceType(Enum):
    ANDROID = 'android'
    IOS = 'ios'
    WINDOWS = 'windows'
    UBUNTU = 'ubuntu'


class BrowserType(Enum):
    CHROME = 'chrome'
    FIREFOX = 'firefox'


class UserAgent:
    """
    UserAgent class.
    Example:
        ua = UserAgent(device=DeviceType.ANDROID, browser=BrowserType.CHROME)
        print(ua)
    """
    def __init__(self, device: DeviceType = DeviceType.ANDROID, browser: BrowserType = BrowserType.CHROME):
        """
        Initialize UserAgent object.

        :param device: Device type, defaults to DeviceType.ANDROID
        :type device: DeviceType
        :param browser: Browser type, defaults to BrowserType.CHROME
        :type browser: BrowserType
        :return: None
        :rtype: None
        """
        self.browser = browser
        self.device = device
        self.browser_version = self.generate_browser_version(browser)
        self.user_agent = self.generate()

    def generate_browser_version(self, browser: BrowserType = BrowserType.CHROME):
        """
        Generate browser version.

        :param browser: Browser type, defaults to BrowserType.CHROME
        :type browser: BrowserType
        :return: Browser version
        :rtype: str
        """
        if self.browser == BrowserType.CHROME:
            chrome_versions = list(range(110, 127))
            major_version = random.choice(chrome_versions)
            minor_version = random.randint(0, 9)
            build_version = random.randint(1000, 9999)
            patch_version = random.randint(0, 99)
            return f"{major_version}.{minor_version}.{build_version}.{patch_version}"
        elif self.browser == BrowserType.FIREFOX:
            firefox_versions = list(range(90, 100))
            return random.choice(firefox_versions)


    def generate(self):
        """
        Generate User-Agent string.

        :return: User-Agent string
        :rtype: str
        """
        if self.device == DeviceType.ANDROID:
            android_versions = ['10.0', '11.0', '12.0', '13.0']
            android_device = random.choice([
                'SM-G960F', 'Pixel 5', 'SM-A505F', 'Pixel 4a', 'Pixel 6 Pro', 'SM-N975F',
                'SM-G973F', 'Pixel 3', 'SM-G980F', 'Pixel 5a', 'SM-G998B', 'Pixel 4',
                'SM-G991B', 'SM-G996B', 'SM-F711B', 'SM-F916B', 'SM-G781B', 'SM-N986B',
                'SM-N981B', 'Pixel 2', 'Pixel 2 XL', 'Pixel 3 XL', 'Pixel 4 XL',
                'Pixel 5 XL', 'Pixel 6', 'Pixel 6 XL', 'Pixel 6a', 'Pixel 7', 'Pixel 7 Pro',
                'OnePlus 8', 'OnePlus 8 Pro', 'OnePlus 9', 'OnePlus 9 Pro', 'OnePlus Nord', 'OnePlus Nord 2',
                'OnePlus Nord CE', 'OnePlus 10', 'OnePlus 10 Pro', 'OnePlus 10T', 'OnePlus 10T Pro',
                'Xiaomi Mi 9', 'Xiaomi Mi 10', 'Xiaomi Mi 11', 'Xiaomi Redmi Note 8', 'Xiaomi Redmi Note 9',
                'Huawei P30', 'Huawei P40', 'Huawei Mate 30', 'Huawei Mate 40', 'Sony Xperia 1',
                'Sony Xperia 5', 'LG G8', 'LG V50', 'LG V60', 'Nokia 8.3', 'Nokia 9 PureView'
            ])
            android_version = random.choice(android_versions)
            if self.browser == BrowserType.CHROME:
                return (f"Mozilla/5.0 (Linux; Android {android_version}; {android_device}) AppleWebKit/537.36 "
                        f"(KHTML, like Gecko) Chrome/{self.browser_version} Mobile Safari/537.36")
            elif self.browser == BrowserType.FIREFOX:
                return (f"Mozilla/5.0 (Android {android_version}; Mobile; rv:{self.browser_version}.0) "
                        f"Gecko/{self.browser_version}.0 Firefox/{self.browser_version}.0")

        elif self.device == DeviceType.IOS:
            ios_versions = ['13.0', '14.0', '15.0', '16.0']
            ios_version = random.choice(ios_versions)
            if self.browser == BrowserType.CHROME:
                return (f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version.replace('.', '_')} like Mac OS X) "
                        f"AppleWebKit/537.36 (KHTML, like Gecko) CriOS/{self.browser_version} Mobile/15E148 Safari/604.1")
            elif self.browser == BrowserType.FIREFOX:
                return (f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version.replace('.', '_')} like Mac OS X) "
                        f"AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/{self.browser_version}.0 Mobile/15E148 Safari/605.1.15")

        elif self.device == DeviceType.WINDOWS:
            windows_versions = ['10.0', '11.0']
            windows_version = random.choice(windows_versions)
            if self.browser == BrowserType.CHROME:
                return (f"Mozilla/5.0 (Windows NT {windows_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        f"Chrome/{self.browser_version} Safari/537.36")
            elif self.browser == BrowserType.FIREFOX:
                return (f"Mozilla/5.0 (Windows NT {windows_version}; Win64; x64; rv:{self.browser_version}.0) "
                        f"Gecko/{self.browser_version}.0 Firefox/{self.browser_version}.0")

        elif self.device == DeviceType.UBUNTU:
            if self.browser == BrowserType.CHROME:
                return (f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                        f"Chrome/{self.browser_version} Safari/537.36")
            elif self.browser == BrowserType.FIREFOX:
                return (f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{self.browser_version}.0) Gecko/{self.browser_version}.0 "
                        f"Firefox/{self.browser_version}.0")

        return None
    def __repr__(self) -> str: 
        """
        Return the User-Agent string representation of the object.

        :return: User-Agent string representation of the object
        :rtype: str
        """
        return self.user_agent


headers_example = {
    'Accept': 'application/json,text/plain,*/*',
    'Accept-Language': 'en-US',
    "Accept-Encoding": "gzip, deflate",
    'Tl-Init-Data': '',
    'Priority': "u=1, i",
    'Origin': 'https://bybitcoinsweeper.com',
    'Referer': 'https://bybitcoinsweeper.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'Sec-Ch-Ua-mobile': '?1',
    'Sec-Ch-Ua-platform': '"Android"',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
}