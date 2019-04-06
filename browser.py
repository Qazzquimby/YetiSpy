import selenium
from selenium.webdriver.chrome.options import Options


class Browser(selenium.webdriver.Chrome):
    def __init__(self):
        options = Options()
        options.headless = True
        super().__init__(options=options, executable_path="chromedriver.exe")
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
