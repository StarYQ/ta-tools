from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
from database import get_scraped_data
import requests
import time
import re
from datetime import datetime

def scrape_hws(username, password, class_input):
    #sets options to run in headless mode
    options = Options()
    options.headless = True
    #sets up webdriver
    driver = webdriver.Chrome(options=options)
    goHome(driver)
    #login
    login(driver, username, password)
    print('Loading...')
    go_to_class(driver, class_input)
    hwNames = curr_hws(driver)
    driver.quit()
    return hwNames

def scrape_data(username, password, class_input, hw_names, hw_input):
    #sets options to run in headless mode
    options = Options()
    options.headless = True
    #sets up webdriver
    with webdriver.Chrome(options=options) as driver:
        goHome(driver)
        #login
        login(driver, username, password)
        print("Loading...")
        #go to class and store student list
        go_to_class(driver, class_input)
        attendance_student_list = store_student_list(driver)
        input_hws = hw_input.split("-")
        input_hw_list = []
        if len(input_hws)==2:
            startIndex = hw_names.index(input_hws[0])
            endIndex = hw_names.index(input_hws[1])
            for i in range(startIndex, endIndex+1):
                input_hw_list.append(hw_names[i])
        else:
            input_hw_list.append(input_hws[0])  
        students_dict = compile_student_lists(driver, input_hw_list, attendance_student_list)
        currTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        driver.quit()
    return {
        'class_name': class_input,
        'student_list': students_dict,
        'homework_names': hw_names,
        'last_scraped': currTime
    }

def post_homework(username, password, class_name, class_type):
    try:
        #sets options to run in headless mode
        options = Options()
        options.headless = True
        #sets up webdriver
        driver = webdriver.Chrome(options=options)
        goHome(driver)
        #login
        login(driver, username, password)
        print('Loading...')
        go_to_class(driver, class_name)
        todays_hw_info = get_todays_hw_info(driver, True)
        for key in todays_hw_info:
            print(key)
        driver.quit()
        name_list = list(todays_hw_info.keys())
        math_hw = name_list[0]
        verbal_hw = name_list[1]
        print(math_hw)
        print(verbal_hw)
        print(todays_hw_info[math_hw][0])
        print(todays_hw_info[math_hw][1])
        print(todays_hw_info[verbal_hw][0])
        print(todays_hw_info[verbal_hw][1])
    except Exception as e:
        print(f"Error processing homework")

def compile_student_lists(driver, hw_names, student_list):
    compiled_lists = {}
    for hw_name in hw_names:
        hw_link = driver.find_element(By.XPATH, f'//a[contains(text(), "{hw_name} ")]') # Space after hw_name to ensure the name matches exactly
        hw_link.click()
        try:
            driver.find_element(By.XPATH, "//a[contains(text(), 'Results') and contains(@role, 'menuitem')]").click()
        except:   
            continue
        submission_list = low_grade_names(driver, hw_name, compiled_lists)
        try:
            for student in student_list:
                if student not in submission_list:
                    if student not in compiled_lists:
                        compiled_lists[student] = {}
                    if "Missing hws" not in compiled_lists[student]:
                        compiled_lists[student]['Missing hws'] = []
                    compiled_lists[student]['Missing hws'].append(hw_name)
        except Exception as e:
            print(f"Error processing homework  '{hw_name}': {e}")
    return compiled_lists

def low_grade_names(driver, hw_name, student_dict):
    max_score_a = driver.find_element(By.XPATH, '//th[contains(@class, "c7 bold")]/a')
    max_score = max_score_a.text.split('Grade/')[1].split()[0]
    submission_page_links = []
    # if driver.find_element(By.XPATH, "(//ul[contains(@class, 'mt-1 pagination ')])[position()=1]"):
    #     pages_ul = driver.find_element(By.XPATH, "(//ul[contains(@class, 'mt-1 pagination ')])[position()=1]")
    #     submission_page_links.extend(pages_ul.find_elements(By.XPATH, "(/li)[position()>1 and position()<last()]"))
    all_attempts = driver.find_elements(By.XPATH, '//tr[contains(@class, "gradedattempt")]')
    # if submission_page_links:
    #     for page in submission_page_links:
    #         page_link = page.find_element(By.XPATH, '/a')
    students_with_submissions = []
    for attempt in all_attempts:
        name_el = attempt.find_element(By.XPATH, './/td[contains(@class, "cell c2 bold")]/a[position()=1]')
        name = name_el.text
        students_with_submissions.append(name)
        score_el = attempt.find_element(By.XPATH, './/td[contains(@class, "cell c7 bold")]')
        score = score_el.text
        if '/' in score:
            score = score.split('/')[1].split()[0]
        score = (float(score)/float(max_score))
        if score == 0:
            students_with_submissions.remove(name)
        elif score<0.5 and score!=0.00: 
        #^change back to 0.5 for normal classes; currently being adjusted manually for class A
            if name not in student_dict:
                student_dict[name] = {}
            if "Low grade hws" not in student_dict[name]:
                student_dict[name]["Low grade hws"] = []
            student_dict[name]['Low grade hws'].append(hw_name + ": " + str(int(round(score, 2)*100))+"%")
    return students_with_submissions

# def find_lows_in_table(student_dict, students_with_submissions, all_attempts, )
    
    
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
        wait_for_element(driver, "(//img[contains(@alt, 'Change attendance')])[position()=1]").click()
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
            #close the tab and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    return due_homework

def curr_hws(driver):
    return get_hw_names_excludingCurrent(driver) + curr_week_hws(driver)

def get_todays_hw_info(driver):
    todays_hws = {}
    now = datetime.now()
    all_currWeek_hws = driver.find_elements(By.XPATH, "(//div[contains(@class, 'current')]//li/a)[position()>1]")
    count = 0
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
                continue
            else:
                due_date_text = due_date_element.text
                due_date_str = due_date_text.split(': ', 1)[1].strip()
                due_date = datetime.strptime(due_date_str, "%A, %d %B %Y, %I:%M %p")
                if due_date > now:
                    print(f"Due date: {due_date}, Now: {now}")
                    count+=1
                    if (count==2):
                        break
                    else:
                        quiz_link = driver.find_element(By.XPATH, "//button[contains(@type, 'submit')]")
                        quiz_link.click()
                        mcq_list = list(driver.find_elements(By.XPATH, "//div[contains(@id, 'question') and contains(@class, 'que multichoice')]"))
                        start_question = mcq_list[0].get_attribute("id").split("-")[2]
                        end_question = mcq_list[len(mcq_list)-1].get_attribute("id").split("-")[2]
                        range = start_question + "-" + end_question
                        todays_hws[hw_name] = [due_date, range]    
        except Exception as e:
            print(f"Error processing homework '{hw_name}': {e}")
        finally:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    return todays_hws

#Generating text message to copy and paste
#************************************************************
def convert_to_string(data):
    #recursively converts all dictionary elements to strings
    if isinstance(data, dict):
        return {str(k): convert_to_string(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [str(item) for item in data]
    else:
        return str(data)

def add_math_or_verbal_to_list(list_name, dict, list1, list2):
    if list_name in dict:
        for hw in dict[list_name]:
            nums = re.findall(r'\d+', hw.lower())
            if 'math' in hw.lower():
                if len(nums)==2:
                    if int(nums[1])<41:
                        list1.append(nums[0])
                else:
                    list1.append(nums[0])
            elif 'verbal' in hw.lower():
                if len(nums)==2:
                    if int(nums[1])<41:
                        list2.append(nums[0])
                else:
                    list2.append(nums[0])

def add_msg_component(num_list, init_str, component_list):
    if len(num_list) > 1:
        hw_nums = ", ".join(num_list)
        component_list.append(f"{init_str}s {hw_nums}")
    elif len(num_list) == 1:
        component_list.append(f"{init_str} {num_list[0]}")

def get_list_msg(data):
    #converts all elements to strings
    student_list_str = convert_to_string(data['student_list'])
    msg = ""
    for student in student_list_str:
        low_grade_math_hws = []
        low_grade_verbal_hws = []
        missing_math_hws = []
        missing_verbal_hws = []
        student_dict = student_list_str[student]

        add_math_or_verbal_to_list('Low grade hws', student_dict, low_grade_math_hws, low_grade_verbal_hws)
        add_math_or_verbal_to_list('Missing hws', student_dict, missing_math_hws, missing_verbal_hws)

        missing_both = list(set(missing_verbal_hws) & set(missing_math_hws))
        missing_math_only = list(set(missing_math_hws) - set(missing_both))
        missing_verbal_only = list(set(missing_verbal_hws) - set(missing_both))
        
        msg_components = []
        add_msg_component(missing_both, 'missing both math and verbal for HW', msg_components)
        add_msg_component(missing_math_only, 'missing math for HW', msg_components)
        add_msg_component(missing_verbal_only, 'missing verbal for HW', msg_components)
        add_msg_component(low_grade_math_hws, 'low grade on math for HW', msg_components)
        add_msg_component(low_grade_verbal_hws, 'low grade on verbal for HW', msg_components)
        #capitalizes first letter of first msg component
        if not msg_components:
            continue
        formatted_name = student.title()
        msg+=f'{formatted_name}: '
        msg_components[0] = msg_components[0][0].upper()+msg_components[0][1:]
        msg+="; ".join(msg_components)
        msg+='\n'
    print(msg)
    return msg