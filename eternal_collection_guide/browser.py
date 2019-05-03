import selenium
from selenium.webdriver.chrome.options import Options


class Browser(selenium.webdriver.Chrome):
    """Context wrapper for selenium Chrome browser."""

    def __init__(self):
        options = Options()
        options.headless = True
        super().__init__(options=options, executable_path="../chromedriver.exe")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
