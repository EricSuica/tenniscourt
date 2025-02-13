#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
import jpholiday
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------
# 配置日志与环境变量
# ---------------------------
LOG_FILE = "tennis_okubo_new.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
load_dotenv("/root/tenniscourt/config.env", override=True)

# 随机等待一段时间，降低请求频率
time.sleep(random.uniform(1, 30))


# ---------------------------
# Selenium 初始化与页面导航
# ---------------------------
def init_driver():
    """初始化并返回配置好的 Chrome WebDriver"""
    options = Options()
    options.add_argument("--headless")  # 无头模式
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
    return webdriver.Chrome(service=service, options=options)


def load_homepage(driver, url):
    """
    加载主页并检查是否为服务休止日。
    如果检测到“本日はサービス休止日となっております”，则退出程序。
    """
    while True:
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "contents")))
            logging.info("主页加载成功")
            # 检查是否为休止日
            try:
                inner_text = driver.find_element(By.ID, "inner-contents").text
                if "本日はサービス休止日となっております" in inner_text:
                    logging.warning("⚠️ 今日是服务休止日，程序终止。")
                    driver.quit()
                    exit(0)
            except NoSuchElementException:
                logging.info("✅ 未发现休止日提示，继续执行。")
            break
        except TimeoutException:
            logging.warning("主页加载超时，正在刷新...")
    time.sleep(random.uniform(1, 3))
    logging.info("初始页面加载完成")


def perform_navigation(driver):
    """
    按照预设步骤依次点击各个按钮/链接，
    直至进入一周空位页面，并返回该页面的HTML源码。
    """
    # 点击“かんたん操作”
    try:
        btn_kantan = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @alt='かんたん操作']"))
        )
        btn_kantan.click()
        logging.info("已点击 'かんたん操作' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（かんたん操作按钮）：%s", e)

    # 点击“空き状況確認”
    try:
        btn_status = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @alt='空き状況確認']"))
        )
        btn_status.click()
        logging.info("已点击 '空き状況確認' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（空き状況確認按钮）：%s", e)

    # 点击 id 为 "button3" 的链接
    try:
        link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "button3"))
        )
        link_button.click()
        logging.info("已点击 'button3' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（button3）：%s", e)

    # 点击 id 为 "id0" 的链接
    try:
        link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id0"))
        )
        link_button.click()
        logging.info("已点击 'id0' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（id0）：%s", e)

    # 点击 id 为 "button0" 的链接
    try:
        link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "button0"))
        )
        link_button.click()
        logging.info("已点击 'button0' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（button0）：%s", e)

    # 点击 title 为 "テニス" 的链接
    try:
        link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@title='テニス']"))
        )
        link_button.click()
        logging.info("已点击 'テニス' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        logging.exception("操作失败（テニス链接）：%s", e)

    # 选择所有复选框（所有曜日）并点击“確定”
    try:
        checkboxes = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//input[@type='checkbox' and @name='chkbox']"))
        )
        for checkbox in checkboxes:
            if not checkbox.is_selected():
                checkbox.click()
        logging.info("已选中所有的曜日复选框")
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnOK"))
        )
        ok_button.click()
        logging.info("已点击 '確定' 按钮，跳转至一天空位页面")
    except Exception as e:
        logging.exception("第一阶段操作失败：%s", e)

    # 点击包含 <img> alt="施設別に切替" 的 <a> 链接，进入一周空位页面
    try:
        link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[img[@alt='施設別に切替']]"))
        )
        link_button.click()
        logging.info("已点击 '施設別に切替' 链接")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[@alt='日付別に切替']"))
        )
        logging.info("一周空位页面加载完成")
        return driver.page_source
    except Exception as e:
        logging.exception("第二阶段操作失败：%s", e)
        return ""


# ---------------------------
# 数据解析与排序
# ---------------------------
def parse_availability(page_html):
    """
    解析一周空位页面的HTML，提取各时间段空位信息。
    返回一个列表，每项为包含 'date' 和 'time' 的字典。
    """
    availability_info = []
    try:
        soup = BeautifulSoup(page_html, "html.parser")
        # 从 <thead> 中提取时间段信息（第一个 <th> 通常为空，其余依次为时间段）
        header_ths = soup.find("thead").find_all("th")
        time_slots = [th.get_text(separator=" ", strip=True) for th in header_ths[1:]]
        
        # 遍历所有 <tbody> 中的行，每一行代表一天
        for tbody in soup.find_all("tbody"):
            tr = tbody.find("tr")
            if not tr:
                continue
            th_date = tr.find("th")
            if not th_date:
                continue
            date_text = th_date.get_text(strip=True)
            # 提取 m/d 格式的日期，例如 "2/13"
            match = re.search(r"(\d+/\d+)", date_text)
            date_str = match.group(1) if match else date_text

            tds = tr.find_all("td")
            for i, td in enumerate(tds):
                img = td.find("img")
                # 当图片的 alt 为 "O" 表示该时段有空位
                if img and img.get("alt") == "O":
                    time_slot = time_slots[i] if i < len(time_slots) else "未知"
                    availability_info.append({"date": date_str, "time": time_slot})
        
        # 定义辅助函数进行排序
        def parse_date(date_str):
            try:
                # 这里假定年份为 2025，如有需要请调整
                return datetime.strptime("2025/" + date_str, "%Y/%m/%d")
            except Exception:
                return datetime.max
        
        def parse_time_slot(time_str):
            match = re.search(r"(\d{2}:\d{2})", time_str)
            return match.group(1) if match else time_str

        availability_info.sort(key=lambda v: (parse_date(v["date"]), parse_time_slot(v["time"])))
        
        for info in availability_info:
            logging.info("空位信息 - 日期: %s, 时间段: %s", info["date"], info["time"])
    except Exception as e:
        logging.exception("解析空位信息失败：%s", e)
    
    return availability_info


# ---------------------------
# 邮件通知
# ---------------------------
def send_email(subject, body):
    """通过 Gmail SMTP 发送邮件通知"""
    sender_email = os.getenv("sender_email2")
    receiver_email = os.getenv("receiver_email").split(",")
    password = os.getenv("password2")
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = "<noreply@example.com>"
    msg["Subject"] = subject
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


def notify_changes(availability_info, last_file="last_availability_okubo_new.txt"):
    """
    将当前预约信息格式化后与上次保存的数据比较，
    如果有变化，则发送邮件通知并更新保存文件。
    """
    # 定义曜日映射（注意此映射顺序需与日期解析保持一致）
    weekday_japanese = ["水", "木", "金", "土", "日", "月", "火"]
    
    # 格式化当前预约信息，每行显示 日期 (星期) | 时间段 | 可预约
    current_availability = "\n".join([
        f"{entry['date']} ({weekday_japanese[datetime.strptime(entry['date'], '%m/%d').weekday()]}) | {entry['time']} | 可预约"
        for entry in availability_info
    ])
    
    if os.path.exists(last_file):
        with open(last_file, "r", encoding="utf-8") as f:
            last_availability = f.read().strip()
    else:
        last_availability = ""
    
    if current_availability and current_availability.strip() != last_availability.strip():
        logging.info("🔔 预约信息发生变化，发送邮件通知")
        email_subject = "🏸 大久保-网球场预约更新通知"
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
    driver = init_driver()
    url = "https://user.shinjuku-shisetsu-yoyaku.jp/regasu/reserve/gin_menu"
    try:
        load_homepage(driver, url)
        page_html = perform_navigation(driver)
        if not page_html:
            logging.error("未能获取一周空位页面的HTML内容。")
            driver.quit()
            exit(1)
        availability_info = parse_availability(page_html)
        notify_changes(availability_info)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
