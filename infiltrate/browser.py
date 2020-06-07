"""Selenium web scraping utilities"""
import json
import pathlib
import sys
import typing as t
import urllib.error
import urllib.request

import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdrivermanager import ChromeDriverManager

current_dir = str(pathlib.Path.cwd())

sys.path.append(current_dir)


class Browser(selenium.webdriver.Chrome):
    """Context wrapper for selenium Chrome browser."""

    driver = None

    def __init__(self):
        if self.driver is None:
            self.driver, _ = ChromeDriverManager(
                download_root=current_dir, link_path=current_dir
            ).download_and_install()

        options = selenium.webdriver.chrome.options.Options()
        options.headless = True

        super().__init__(self.driver, options=options)

    def safely_find(self, finder):
        """Waits up to max_delay for the finder to find an element."""
        max_delay = 5
        element = WebDriverWait(self, max_delay).until(finder)
        return element

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_strs_from_url_and_xpath(url: str, xpath: str) -> t.List[str]:
    """Get a list of elements found at the xpath at the url."""
    with Browser() as browser:
        browser.get(url)
        elements = browser.safely_find(lambda x: x.find_elements_by_xpath(xpath))
        texts = [element.text for element in elements]
    return texts


def get_str_from_url_and_xpath(url: str, xpath: str) -> str:
    """Get the text from an element specified by the xpath at the url."""
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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/35.0.1916.47 Safari/537.36 "
        },
    )

    try:
        page = urllib.request.urlopen(request)
        page_string = page.read().decode("utf-8")
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
