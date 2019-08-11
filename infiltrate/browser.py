"""Selenium web scraping utilities"""
import json
import urllib.error
import urllib.request

import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Browser(selenium.webdriver.Chrome):
    """Context wrapper for selenium Chrome browser."""

    def __init__(self):
        options = selenium.webdriver.chrome.options.Options()
        options.headless = True
        super().__init__(options=options, executable_path="chromedriver.exe")

    def safely_find(self, finder):
        """Waits up to max_delay for the finder to find an element."""
        max_delay = 5
        element = WebDriverWait(self, max_delay).until(finder)
        return element

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_str_from_url_and_xpath(url: str, xpath: str):
    """Gets the text from an element specified by the xpath at the url."""
    with Browser() as browser:
        browser.get(url)
        element = browser.safely_find(lambda x: x.find_element_by_xpath(xpath))
        result = element.text
    return result


def obj_from_url(url: str):
    """Returns the page at the given url as JSON"""
    request = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/35.0.1916.47 Safari/537.36 '
        }
    )

    try:
        page = urllib.request.urlopen(request)
        page_string = page.read().decode('utf-8')
        page_json = json.loads(page_string)
    except urllib.error.URLError:
        page_json = None

    # page_json could be None if page loads as empty
    if page_json is None:
        raise ConnectionError(f"Got no content from {url}")
    return page_json

    # response = requests.get(url)
    # if response.status_code == 500: todo implement error test
    #     raise BadKeyException
    # response_json = json.loads(response.text)
