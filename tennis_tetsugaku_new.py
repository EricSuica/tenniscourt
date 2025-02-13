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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)

from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------
# 配置日志与环境变量
# ---------------------------
LOG_FILE = "tennis_tetsugaku_new.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
load_dotenv("/root/tenniscourt/config.env", override=True)

# 随机等待，降低请求频率
time.sleep(random.uniform(1, 30))


# ---------------------------
# Selenium 初始化与导航步骤
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
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def wait_for_element(driver, by, locator, timeout=10):
    """封装等待元素出现"""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, locator))
    )


def perform_navigation(driver):
    """
    按照预设步骤点击各个按钮/链接，直至进入时间预约页面
    """
    base_url = "https://yoyaku.nakano-tokyo.jp/stagia/reserve/grb_init"
    driver.get(base_url)
    # 等待主页加载（id="contents"出现）
    while True:
        try:
            wait_for_element(driver, By.ID, "contents", timeout=10)
            logging.info("主页加载成功")
            break
        except TimeoutException:
            logging.warning("主页加载超时，正在刷新...")
            driver.get(base_url)

    time.sleep(random.uniform(1, 3))
    logging.info("初始页面加载完毕")

    # ===== 第1阶段：选择预约状态 =====
    try:
        # 点击“空き状況確認”按钮（图片按钮）
        btn_check = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//input[@type='image' and contains(@src, 'btn_check_status_01.gif')]"
            ))
        )
        btn_check.click()
        logging.info("已点击 '空き状況確認' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "allChecked")))
    except Exception as e:
        logging.exception("操作失败（空き状況確認按钮）：%s", e)

    # ===== 第2阶段：分类选择1 =====
    try:
        btn_all_checked = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "allChecked"))
        )
        btn_all_checked.click()
        logging.info("已点击 '全て' 按钮")
        # 等待按钮变为 active 状态
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@id='allChecked' and contains(@class, 'active')]")
            )
        )
        logging.info("'全て' 按钮已激活")
    except Exception as e:
        logging.exception("操作失败（全て）：%s", e)

    try:
        # 点击“確定”按钮（第一处）
        btn_ok = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]")
            )
        )
        btn_ok.click()
        logging.info("已点击第1处 '確定' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "button2")))
    except Exception as e:
        logging.exception("操作失败（第1处 確定）：%s", e)

    # ===== 第3阶段：分类选择2 =====
    try:
        # 点击链接按钮 "運動施設"（id="button2"）
        btn_sport = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "button2"))
        )
        btn_sport.click()
        logging.info("已点击 '運動施設' 按钮")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@id='button2' and contains(@class, 'active')]")
            )
        )
        logging.info("'運動施設' 按钮已激活")
    except Exception as e:
        logging.exception("操作失败（運動施設）：%s", e)

    try:
        # 点击“確定”按钮（第二处）
        btn_ok = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]")
            )
        )
        btn_ok.click()
        logging.info("已点击第2处 '確定' 按钮")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-page-next.gif')]")
            )
        )
    except Exception as e:
        logging.exception("操作失败（第2处 確定）：%s", e)

    # ===== 第4阶段：目的选择 =====
    try:
        # 点击“次頁”按钮（id="nextButton"）
        btn_next = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "nextButton"))
        )
        btn_next.click()
        logging.info("已点击 '次頁' 按钮")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '硬式テニス')]"))
        )
        logging.info("页面已出现 '硬式テニス'")
    except Exception as e:
        logging.exception("操作失败（次頁）：%s", e)

    try:
        # 点击“硬式テニス”链接
        btn_tennis = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '硬式テニス')]"))
        )
        btn_tennis.click()
        logging.info("已点击 '硬式テニス' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id0")))
        logging.info("页面已出现 '哲学堂運動施設'")
    except Exception as e:
        logging.exception("操作失败（硬式テニス）：%s", e)

    try:
        # 点击“哲学堂運動施設”按钮（id="id0"）
        btn_facility = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id0"))
        )
        btn_facility.click()
        logging.info("已点击 '哲学堂運動施設' 按钮")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@id='id0' and contains(@class, 'active')]")
            )
        )
        logging.info("'哲学堂運動施設' 按钮已激活")
    except Exception as e:
        logging.exception("操作失败（哲学堂運動施設）：%s", e)

    try:
        # 点击“確定”按钮（第三处）
        btn_ok = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnOk"))
        )
        btn_ok.click()
        logging.info("已点击第3处 '確定' 按钮")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "button0")))
        logging.info("页面已出现 '庭球場第１コート'")
    except Exception as e:
        logging.exception("操作失败（第3处 確定）：%s", e)

    try:
        # 点击“全て”按钮（再次选择全部，id="allChecked"）
        btn_all_checked = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "allChecked"))
        )
        btn_all_checked.click()
        logging.info("已点击 '全て' 按钮（第二次）")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@id='allChecked' and contains(@class, 'active')]")
            )
        )
        logging.info("'全て' 按钮已激活（第二次）")
    except Exception as e:
        logging.exception("操作失败（全て，第二次）：%s", e)

    try:
        # 点击“確定”按钮（第四处）
        btn_ok = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]")
            )
        )
        btn_ok.click()
        logging.info("已点击第4处 '確定' 按钮")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filter-by-day"))
        )
        logging.info("页面已出现 '曜　日を絞る'")
    except Exception as e:
        logging.exception("操作失败（第4处 確定）：%s", e)

    # ===== 第5阶段：选择显示开始日期与星期 =====
    select_date(driver)
    select_weekdays(driver)

    try:
        # 点击“確定”按钮，进入一周时间显示页面
        btn_ok = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-nav-change.gif')]")
            )
        )
        btn_ok.click()
        logging.info("已点击 '確定' 按钮，进入一周时间表示页面")
        # 可在此处增加等待确认页面加载的逻辑
    except Exception as e:
        logging.exception("操作失败（最后 確定）：%s", e)


def select_date(driver):
    """
    选择今天的日期
    通过动态构造 XPath 找到 onclick 包含今天日期（格式 YYYYMMDD）的 <td> 元素并点击
    """
    try:
        today_str = datetime.today().strftime("%Y%m%d")
        logging.info(f"今天的日期是：{today_str}")
        date_xpath = f"//td[contains(@onclick, 'dateClick') and contains(@onclick, '{today_str}')]"
        date_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, date_xpath))
        )
        date_button.click()
        logging.info(f"已点击今天的日期按钮（{today_str}）")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"{date_xpath}[contains(@class, 'active')]"))
        )
        logging.info(f"日期按钮（{today_str}）已变为 active 状态")
    except Exception as e:
        logging.exception("操作失败（日期选择）：%s", e)


def select_weekdays(driver):
    """
    遍历点击 id 为 img0 ~ img7 的元素（选择星期）
    """
    try:
        for i in range(8):
            img_id = f"img{i}"
            logging.info(f"尝试点击 {img_id}")
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, img_id))
            )
            btn.click()
            logging.info(f"已点击 {img_id}")
            time.sleep(1)
    except Exception as e:
        logging.exception("操作失败（点击星期按钮 img0 - img7）：%s", e)


# ---------------------------
# 页面解析与数据提取
# ---------------------------
def parse_schedule(driver):
    """
    解析当前及后续页面，提取所有空位信息
    返回所有可预约时段的列表，每项为 dict，包含 'date', 'facility' 和 'time'
    """
    all_slots = []

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # 提取当前日期
        today_date = extract_date(soup)
        logging.info(f"当前页面日期：{today_date}")

        # 提取设施名称（tbody中每行第一列的 <strong> 文本）
        facilities = [elem.get_text(strip=True) for elem in soup.select("tbody tr th strong")]

        # 提取时间段（thead中 id 以 td10_ 开头的 th，替换掉 "～" 为 "-"）
        time_slots = [
            header.get_text(strip=True).replace("～", "-")
            for header in soup.select("thead tr th[id^='td10_']")
        ]

        # 提取各设施在各时段的空位情况
        facility_rows = soup.select("tbody tr")
        for idx, row in enumerate(facility_rows):
            if idx >= len(facilities):
                continue
            facility_name = facilities[idx]
            # 选择各个时段对应的单元格（id 以 td11_ ~ td16_）
            cells = row.select("td[id^='td11_'], td[id^='td12_'], td[id^='td13_'], td[id^='td14_'], td[id^='td15_'], td[id^='td16_']")
            for t_index, cell in enumerate(cells):
                img = cell.find("img")
                if img and any(x in img["src"] for x in ["icon_timetable_sankaku.gif", "icon_timetable_O.gif"]):
                    slot = {
                        "date": today_date,
                        "facility": facility_name,
                        "time": time_slots[t_index] if t_index < len(time_slots) else "未知时段",
                    }
                    all_slots.append(slot)

        # 尝试点击 "次へ" 按钮进入下一天
        try:
            next_btn = driver.find_element(By.XPATH, "//img[@alt='次へ']")
            next_btn.click()
            time.sleep(1)  # 等待页面加载
        except ElementNotInteractableException:
            logging.info("已到达最后一天，停止获取。")
            break

    return all_slots


def extract_date(soup):
    """
    从页面中解析日期信息，形如 "令和07年2月8日(土)"，转换为 YYYY-MM-DD 格式
    """
    date_elem = soup.select_one("li.day#li")
    if date_elem:
        raw_date = date_elem.get_text(strip=True)
        match = re.search(r"令和(\d+)年(\d+)月(\d+)日", raw_date)
        if match:
            reiwa_year, month, day = map(int, match.groups())
            western_year = 2018 + reiwa_year  # 令和元年为2019
            return f"{western_year}-{month:02d}-{day:02d}"
    return "未知日期"


def filter_slots(slots):
    """
    根据预约规则进行过滤：
      - 平日只保留 19:00-21:00 的时段
      - 祝日及周六/周日保留所有时段
    返回符合条件的预约项列表
    """
    filtered = []
    for slot in slots:
        try:
            date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
        except Exception:
            continue
        weekday = date_obj.weekday()  # 0: Monday ... 6: Sunday
        is_holiday = jpholiday.is_holiday(date_obj) or weekday in [5, 6]
        # 平日仅保留 19:00-21:00 时段
        if not is_holiday and slot["time"] == "19:00-21:00":
            filtered.append(slot)
        elif is_holiday:
            filtered.append(slot)
    return filtered


# ---------------------------
# 邮件通知相关函数
# ---------------------------
def send_email(subject, body):
    """通过 Gmail SMTP 发送邮件通知"""
    sender_email = os.getenv("sender_email2")
    receiver_emails = os.getenv("receiver_email").split(",")
    password = os.getenv("password2")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = "<noreply@example.com>"
    msg["Subject"] = subject
    msg["Bcc"] = ", ".join(receiver_emails)
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


def notify_if_changed(filtered_slots, last_file="last_availability_tetsugaku_new.txt"):
    """
    将当前预约信息格式化后与上次保存的数据比较，
    若有变化则发送邮件通知并更新保存文件
    """
    WEEKDAY_JAPANESE = ["月", "火", "水", "木", "金", "土", "日"]

    # 格式化当前预约信息（带星期）
    current_info = "\n".join(
        f"{slot['date']} ({WEEKDAY_JAPANESE[datetime.strptime(slot['date'], '%Y-%m-%d').weekday()]}) | {slot['time']} | {slot['facility']}"
        for slot in filtered_slots
    )

    # 读取上次保存的信息
    if os.path.exists(last_file):
        with open(last_file, "r", encoding="utf-8") as f:
            last_info = f.read().strip()
    else:
        last_info = ""

    if current_info.strip() != last_info.strip():
        logging.info("🔔 预约信息发生变化，发送邮件通知")
        subject = "🏸 哲学堂-网球场预约更新通知"
        body = "本次查询到的可预约时间如下：\n\n" + current_info
        send_email(subject, body)
        with open(last_file, "w", encoding="utf-8") as f:
            f.write(current_info)
    else:
        logging.info("✅ 预约信息无变化，不发送邮件")


# ---------------------------
# 主流程
# ---------------------------
def main():
    driver = init_driver()

    try:
        # 按照流程依次点击各个按钮/链接
        perform_navigation(driver)
        # 解析页面获取所有空位信息
        all_slots = parse_schedule(driver)
        logging.info(f"共获取到 {len(all_slots)} 条预约信息")

        # 筛选符合预约条件的时段
        filtered_slots = filter_slots(all_slots)
        if not filtered_slots:
            logging.warning("⚠️ 未找到符合条件的空位，程序终止。")
            driver.quit()
            exit(0)

        logging.info("🎾 筛选后的可预约信息：")
        for slot in filtered_slots:
            logging.info(f"{slot['date']} | {slot['facility']} | {slot['time']}")

        # 比较新旧数据，若有变化则发送邮件通知
        notify_if_changed(filtered_slots)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
