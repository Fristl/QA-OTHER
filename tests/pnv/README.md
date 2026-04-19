# Начало работы

## 1. Установка виртуального окружения
uv sync

## 2. Appium Inspector
`appium plugin install inspector`  
`appium --use-plugins=inspector`  

## 3. Appium Server
Запуск сервера: `appium`  

## 4. Необходимое ПО
- Android Studio  
- Android SDK  
- JDK  

## 5. Запуск allure
pytest --alluredir=allure_reports ./tests/pnv 
allure serve allure_reports
