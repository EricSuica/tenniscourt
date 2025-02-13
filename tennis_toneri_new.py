#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import random
import logging
import smtplib
import os
import shutil
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import jpholiday

# ---------------------------
# 配置日志和加载环境变量
# ---------------------------
logging.basicConfig(
    filename="tennis_toneri_new.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
load_dotenv("/root/tenniscourt/config.env", override=True)

# 随机等待一段时间，降低频率
time.sleep(random.uniform(1, 30))


# ---------------------------
# Selenium 相关函数
# ---------------------------
def initialize_driver():
    options = Options()
    options.add_argument("--headless")  # 如需调试可去掉此行
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def load_home_page(driver, url):
    while True:
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "btn-go"))
            )
            logging.info("主页加载成功")
            break
        except TimeoutException:
            logging.warning("主页加载超时，正在刷新...")


def select_sport_and_park(driver):
    # 选择种目
    sport_select = Select(driver.find_element(By.ID, "purpose-home"))
    sport_select.select_by_value("1000_1030")  # "テニス（人工芝）"
    logging.info("種目选择成功")

    # 等待公园选项加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[@id='bname-home']/option[@value='1140']")
        )
    )
    logging.info("公园选项加载成功")

    # 选择公园
    park_select = Select(driver.find_element(By.ID, "bname-home"))
    park_select.select_by_value("1140")  # "舎人公園"
    logging.info("公园选择成功")


def click_search_button(driver, initial_url):
    search_button = driver.find_element(By.ID, "btn-go")
    search_button.click()
    logging.info("搜索按钮点击成功")

    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            WebDriverWait(driver, 20).until(lambda d: d.current_url != initial_url)
            logging.info("页面跳转成功")
            break
        except TimeoutException:
            retry_count += 1
            logging.error(
                f"页面跳转超时，正在重试 ({retry_count}/{max_retries})"
            )
            if retry_count == max_retries:
                logging.error("页面跳转失败，达到最大重试次数，退出")
                driver.quit()
                exit()
            time.sleep(3)


def wait_for_month_info(driver):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "loadedmonth"))
            )
            logging.info("月份信息加载成功")
            break
        except TimeoutException:
            retry_count += 1
            logging.error(
                f"月份信息加载失败，正在重试 ({retry_count}/{max_retries})"
            )
            if retry_count == max_retries:
                logging.error("月份信息加载失败，达到最大重试次数，退出")
                driver.quit()
                exit()
            time.sleep(3)


def expand_month_info(driver):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            expand_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "span-icon-down"))
            )
            expand_button.click()
            logging.info("点击展开月份按钮")
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "month-info"))
            )
            logging.info("月份信息已展开")
            break
        except TimeoutException:
            retry_count += 1
            logging.error(
                f"月份信息展开失败，正在重试 ({retry_count}/{max_retries})"
            )
            if retry_count == max_retries:
                logging.error("月份信息展开失败，达到最大重试次数，退出")
                driver.quit()
                exit()
            time.sleep(3)
        except NoSuchElementException:
            logging.warning("找不到展开按钮，可能已经展开")
            break


def click_date_and_extract(driver, date, availability_info):
    """点击指定日期并提取该日的时段空位信息"""
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts:
        try:
            attempt += 1
            logging.info(f"🔄 第 {attempt} 次点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            # 重新定位日期元素
            date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"month_{date}"))
            )
            date_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, f"month_{date}"))
            )
            date_element.click()
            logging.info(f"✅ 成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            time.sleep(2)  # 等待 JS 渲染

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "week-info"))
            )
            logging.info(f"✅ {date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

            html_after_click = driver.execute_script("return document.body.outerHTML;")
            # 清除当前日期旧数据
            availability_info = {k: v for k, v in availability_info.items() if k[0] != date}

            pattern_slots = re.compile(
                r'<input id="A_(\d{8})_(\d{2})" type="hidden" value="(\d+)">',
                re.S
            )
            for match in pattern_slots.finditer(html_after_click):
                slot_date, slot_suffix, available_count = match.groups()
                if slot_date == date:
                    slot_time = {
                        "10": "9-11点", "20": "11-13点",
                        "30": "13-15点", "40": "15-17点",
                        "50": "17-19点", "60": "19-21点"
                    }.get(slot_suffix, "未知时间段")
                    availability_info[(slot_date, slot_time)] = available_count
            break  # 成功后退出重试循环
        except StaleElementReferenceException:
            logging.warning(f"⚠️ 目标元素失效，重试点击 {date[:4]}年{date[4:6]}月{date[6:]}日...")
            time.sleep(1)
        except TimeoutException:
            logging.error(f"❌ 无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            driver.quit()
            exit(0)
    return availability_info


def extract_available_dates(html):
    """
    使用正则表达式提取页面中可预约的日期，
    返回：完全空闲日期列表、部分空闲日期列表
    """
    pattern = re.compile(
        r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?'
        r'<img[^>]*?alt="(全て空き|一部空き)"',
        re.S
    )
    available_dates = []
    partially_available_dates = []
    for match in pattern.finditer(html):
        date_number, status = match.groups()
        if status == "全て空き":
            available_dates.append(date_number)
        elif status == "一部空き":
            partially_available_dates.append(date_number)
    return available_dates, partially_available_dates


def filter_holidays_and_weekends(dates):
    """过滤出日本的休日（周六、周日或祝日）的日期"""
    def is_holiday_or_weekend(date_str):
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)
    return [date for date in dates if is_holiday_or_weekend(date)]


# ---------------------------
# 邮件发送相关函数
# ---------------------------
def send_email(subject, body):
    sender_email = os.getenv("sender_email2")  # 你的 Gmail 地址
    receiver_email = os.getenv("receiver_email").split(",")  # 收件人邮箱列表
    password = os.getenv("password2")  # Gmail 应用专用密码

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = "<noreply@example.com>"
    msg["Subject"] = subject
    # 使用密送避免暴露收件人地址
    msg["Bcc"] = ', '.join(receiver_email)
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        logging.info("📧 邮件发送成功")
    except Exception as e:
        logging.error(f"❌ 邮件发送失败: {e}")


def process_email_notification(availability_info):
    """比较最新预约信息与上次保存的内容，如有变化则发送邮件通知，并更新文件"""
    last_file = "last_availability_toneri_new.txt"
    if os.path.exists(last_file):
        with open(last_file, "r", encoding="utf-8") as f:
            last_availability = f.read()
    else:
        last_availability = ""

    # 按照日期和时间段排序
    time_order = {"9-11点": 1, "11-13点": 2, "13-15点": 3, "15-17点": 4, "17-19点": 5, "19-21点": 6}
    sorted_availability = sorted(
        availability_info.items(),
        key=lambda x: (x[0][0], time_order.get(x[0][1], 99))
    )

    weekday_japanese = ["月", "火", "水", "木", "金", "土", "日"]
    current_availability = "\n".join(
        f"{date[:4]}-{date[4:6]}-{date[6:]} ({weekday_japanese[datetime.strptime(date, '%Y%m%d').weekday()]}) | {time_slot} | 可预约：{count} 人"
        for (date, time_slot), count in sorted_availability
    )

    if current_availability.strip() != last_availability.strip():
        logging.info("🔔 预约信息发生变化，发送邮件通知")
        email_subject = "🏸 舍人-网球场预约更新通知"
        email_body = "本次查询到的可预约时间如下：\n\n" + current_availability
        send_email(email_subject, email_body)
        with open(last_file, "w", encoding="utf-8") as f:
            f.write(current_availability)
    else:
        logging.info("✅ 预约信息无变化，不发送邮件")


# ---------------------------
# 主流程
# ---------------------------
def main():
    url = "https://kouen.sports.metro.tokyo.lg.jp/web/index.jsp"
    driver = initialize_driver()

    # 访问主页并等待搜索按钮加载
    load_home_page(driver, url)
    time.sleep(random.uniform(1, 3))
    logging.info("搜索按钮加载成功")

    # 选择种目和公园
    select_sport_and_park(driver)

    # 点击搜索按钮并等待页面跳转
    click_search_button(driver, url)

    # 等待月份信息加载
    wait_for_month_info(driver)
    expand_month_info(driver)

    # 获取当前页面 HTML 和月份信息
    html_current = driver.execute_script("return document.body.outerHTML;")
    month_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "month-head"))
    )
    month_text = month_element.text

    # 提取当前月可预约日期（完全空闲和部分空闲）
    curr_available, curr_partially = extract_available_dates(html_current)
    logging.info(f"{month_text}可预约的日期（完全空闲）：{curr_available}")
    logging.info(f"{month_text}可预约的日期（部分空闲）：{curr_partially}")

    # 过滤出仅休日/祝日
    curr_available = filter_holidays_and_weekends(curr_available)
    curr_partially = filter_holidays_and_weekends(curr_partially)
    logging.info(f"{month_text}可预约的日期（仅休日&祝日，完全空闲）：{curr_available}")
    logging.info(f"{month_text}可预约的日期（仅休日&祝日，部分空闲）：{curr_partially}")

    # 若未找到部分空闲则退出
    if not curr_partially:
        logging.warning(f"{month_text} ⚠️ 未找到空位，程序终止。")
        driver.quit()
        exit(0)

    availability_info = {}

    # 处理当前月所有可预约日期
    for date in curr_available + curr_partially:
        logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")
        availability_info = click_date_and_extract(driver, date, availability_info)

    # 处理下月数据
    try:
        next_month_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "next-month"))
        )
        next_month_button.click()
        logging.info("已点击按钮 '下月'，进入新页面")
        time.sleep(5)
        month_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "month-head"))
        )
        month_text_next = month_element.text
        logging.info(f"✅ 已出现 下月信息: {month_text_next}")
    except Exception as e:
        logging.exception("操作失败（下月）：%s", e)

    html_next = driver.execute_script("return document.body.outerHTML;")
    next_available, next_partially = extract_available_dates(html_next)

    if not next_available:
        logging.info(f"⚠️ {month_text_next} 空位未开放查询")
    else:
        logging.info(f"{month_text_next}可预约的日期（完全空闲）：{next_available}")
        logging.info(f"{month_text_next}可预约的日期（部分空闲）：{next_partially}")

        next_available = filter_holidays_and_weekends(next_available)
        next_partially = filter_holidays_and_weekends(next_partially)
        logging.info(f"{month_text_next}可预约的日期（仅休日&祝日，完全空闲）：{next_available}")
        logging.info(f"{month_text_next}可预约的日期（仅休日&祝日，部分空闲）：{next_partially}")

        for date in next_available + next_partially:
            logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")
            availability_info = click_date_and_extract(driver, date, availability_info)

    # 输出最终可预约信息
    logging.info("所有可预约时间段:")
    for (date, time_slot), count in availability_info.items():
        logging.info(f"{date} | {time_slot} | 可预约：{count} 人")

    driver.quit()

    # 邮件通知
    process_email_notification(availability_info)


if __name__ == "__main__":
    main()
