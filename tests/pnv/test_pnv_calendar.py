import os

import allure
import pytest
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import time
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver

class MyListener(AbstractEventListener):
    def before_find(self, by, value, driver) -> None:
        print(f'Finding {by} {value}')
        super().before_find(by, value, driver)
    def before_click(self, element, driver) -> None:
        print(f'click on {element}')


appium_server_url = 'http://localhost:4723'
# APK лежит рядом в директории
default_apk = os.path.abspath(os.path.join(os.path.dirname(__file__), "pnv.apk"))
PNV_APP_PATH = default_apk

options = AppiumOptions()
options.load_capabilities({
    'platformName': "Android",
    'automationName': "UiAutomator2",
    'appium:app': PNV_APP_PATH,
})


@pytest.fixture()
def driver():
    android_driver = webdriver.Remote(appium_server_url, options=options)
    yield android_driver
    android_driver.quit()


@allure.feature("Swipe Test")
@allure.story("Swipe to Calendar")
def test_swipe_to_calendar(driver):
    Listener_driver = EventFiringWebDriver(driver, MyListener())
    with allure.step("Перейти в таб user apps"):
        driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("USER APPS")'
        ).click()
        time.sleep(11)


    while True:
        elements = Listener_driver.find_elements(AppiumBy.ID, "com.csdroid.pkg:id/tv_title")
        print(elements[0].rect)

        with allure.step("Поиск элементов"):
            Listener_driver.swipe(elements[1].rect['x'], elements[1].rect['y'],
                         elements[0].rect['x'], elements[0].rect['y'])

            elements = Listener_driver.find_elements(AppiumBy.ID, "com.csdroid.pkg:id/tv_title")
            element_names = [el.text for el in elements]
            print(element_names)

            if 'Calendar' in element_names:
                break

    with allure.step("Тест завершен — Calendar найден"):
        pass
