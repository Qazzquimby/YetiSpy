import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Browser(selenium.webdriver.Chrome):
    """Context wrapper for selenium Chrome browser."""

    def __init__(self):
        options = selenium.webdriver.chrome.options.Options()
        options.headless = True
        super().__init__(options=options, executable_path="../chromedriver.exe")

    def safely_find(self, finder):
        max_delay = 5
        element = WebDriverWait(self, max_delay).until(finder)
        return element

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
