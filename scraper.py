from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def scrape_data(username, password, class_input):
    # Set options to run in headless mode
    options = Options()
    options.headless = True

    # Set up webdriver
    driver = webdriver.Chrome(options=options)
    goHome(driver)

    # Login
    login(driver, username, password)
    print("Loading...")

    # Go to class and store student list
    class_name = go_to_class(driver, class_input)
    student_list = store_student_list(driver)
    
    # Get homework names
    hwNames = curr_hws(driver)
    currTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    driver.quit()

    # Return the scraped data
    return {
        'class_name': class_input,
        'student_list': student_list,
        'homework_names': hwNames,
        'last_scraped': currTime
    }

def goHome(driver):
    driver.get('https://class.abcmath.com/class/my/')

def wait_for_element(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

def wait_for_elements(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))

def find_and_fill(driver, element_id, info):
    element = driver.find_element(By.ID, element_id)
    element.send_keys(info)

def login(driver, username, password):
    find_and_fill(driver, "username", username)
    find_and_fill(driver, "password", password)
    driver.find_element(By.ID, "loginbtn").click()

def go_to_class(driver, class_input):
    try:
        ul_el = wait_for_element(driver, "//ul[@class='unlist']")
        list_items = ul_el.find_elements(By.XPATH, ".//li")
        class_list = {}
        for item in list_items:
            anchor = item.find_element(By.XPATH, ".//a")
            title = anchor.get_attribute("title")
            titleParts = []
            if "SUM" in title:
                titleParts = title.split("SUM")
            elif "FAL" in title:
                titleParts = title.split("FAL")
            else:
                titleParts = title.split("SPR")
            titleParts[1] = re.sub(r'\d', '', titleParts[1])
            class_name = titleParts[0] + titleParts[1]
            class_list[class_name] = title
        for key in class_list.keys():
            print(key)
        class_name = class_list[class_input]
        class_found = False
        for item in list_items:
            anchor = item.find_element(By.XPATH, ".//a")
            title = anchor.get_attribute("title")
            if str(title).lower() == str(class_name).lower():
                print(f'Selecting class: {title}')
                anchor.click()
                class_found = True
                break
        if not class_found:
            print("Class not found")
        return class_name
    except Exception as e:
        print(f"Error in go_to_class: {e}")
        return None

def store_student_list(driver):
    try:
        wait_for_element(driver, "//a[contains(text(), 'Attendance')]").click()
        wait_for_element(driver, "//a[contains(text(), 'Months')]").click()
        wait_for_element(driver, "//table[@class='generaltable']/tbody/tr/td[contains(@class, 'lastcol')]/a[@class='action-icon']/img[@alt='Change attendance']/..").click()
        student_table = wait_for_element(driver, "//table[@class='generaltable takelist']")
        soup = BeautifulSoup(student_table.get_attribute('outerHTML'), 'html.parser')
        student_list = [a.text for a in soup.select('tbody tr:not(:first-child) td:first-child a:nth-of-type(2)')]
        return student_list
    except Exception as e:
        print(f"Error in store_student_list: {e}")
        return []

def get_hw_names_excludingCurrent(driver):
    hw_names=[]
    week_divs = wait_for_elements(driver, "(//div[contains(@class, 'courseindex-section') and not(contains(@class, 'courseindex-item'))])[position()>1 and position()<last()]")
    for div in week_divs:
        if "current" in div.get_attribute("class"):
            break
        week = div.find_element(By.XPATH, ".//ul")
        hw_anchors= week.find_elements(By.XPATH, "./li[position()>2]/a")
        for a in hw_anchors:
            text = a.text.strip()
            if "quiz" in text.lower():
                continue
            text = re.sub(r'\bTurn in\b', '', text)
            text = re.sub(r'\bhere\b', '', text)
            text = re.sub(r'\s+', ' ', text).strip()  # Ensure extra spaces are removed
            hw_names.append(text)
    return hw_names

def curr_week_hws(driver):
    due_homework = []
    now = datetime.now()
    all_currWeek_hws = driver.find_elements(By.XPATH, "(//div[contains(@class, 'current')]//li/a)[position()>1]")
    for hw in all_currWeek_hws:
        hw_name = hw.text.strip()
        hw_link = hw.get_attribute('href')
        if "quiz" in hw_name.lower():
            continue
        #filter hw name
        hw_name = re.sub(r'\bTurn in\b', '', hw_name)
        hw_name = re.sub(r'\bhere\b', '', hw_name)
        hw_name = re.sub(r'\s+', ' ', hw_name).strip()
        #open hw page in new tab
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(hw_link)
        try:
            due_date_element = wait_for_element(driver, "//div/strong[contains(., 'Closed:') or contains(., 'Closes:') or contains(., 'Due:')]/..") 
            if due_date_element.find_elements(By.XPATH, "./strong[contains(., 'Closed:')]"):
                due_homework.append(hw_name)
            else:
                due_date_text = due_date_element.text
                due_date_str = due_date_text.split(': ', 1)[1].strip()
                due_date = datetime.strptime(due_date_str, "%A, %d %B %Y, %I:%M %p")
                if due_date <= now:
                    due_homework.append(hw_name)
                    print(f"Due date: {due_date}, Now: {now}")
                else:
                    break
        except Exception as e:
            print(f"Error processing homework '{hw_name}': {e}")
        finally:
            # Close the tab and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    return due_homework

def curr_hws(driver):
    return get_hw_names_excludingCurrent(driver) + curr_week_hws(driver)