import re
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import jpholiday
from datetime import datetime
load_dotenv("/root/tenniscourt/config.env")

# 设置日志
logging.basicConfig(
    filename="tennis_toneri.log",  # 输出到文件
    level=logging.INFO,  # 记录 INFO 及以上级别的日志
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 1️⃣ 配置 Selenium
options = Options()
options.add_argument("--headless")  # 可去掉调试
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")  
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")  

# 2️⃣ 启动 WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 3️⃣ **访问主页并检测超时**
url = "https://kouen.sports.metro.tokyo.lg.jp/web/index.jsp"

while True:  # **无限循环直到访问成功**
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "btn-go"))
        )
        logging.info("主页加载成功")
        break
    except TimeoutException:
        logging.warning("主页加载超时，正在刷新...")

time.sleep(random.uniform(1, 3))
logging.info("搜索按钮加载成功")

# 5️⃣ 选择 種目（选择 "テニス（ハード）"）
sport_select = Select(driver.find_element(By.ID, "purpose-home"))
sport_select.select_by_value("1000_1030")  # "テニス（人工芝）"
logging.info("種目选择成功")

# 6️⃣ **等待 JavaScript 更新公园选项**
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//select[@id='bname-home']/option[@value='1140']"))
)
logging.info("公园选项加载成功")

# 7️⃣ 选择 公園（选择 "舎人公園"）
park_select = Select(driver.find_element(By.ID, "bname-home"))
park_select.select_by_value("1140")
logging.info("公园选择成功")

# 8️⃣ **点击搜索按钮**
search_button = driver.find_element(By.ID, "btn-go")
search_button.click()
logging.info("搜索按钮点击成功")

# **等待 URL 变化**
max_retries = 3  # 允许最多重试 3 次
retry_count = 0

while retry_count < max_retries:
    try:
        WebDriverWait(driver, 20).until(lambda driver: driver.current_url != url)
        logging.info("页面跳转成功")
        break  # ✅ 成功，跳出循环
    except TimeoutException:
        retry_count += 1
        logging.error(f"页面跳转超时，正在重试 ({retry_count}/{max_retries})")
        if retry_count == max_retries:
            logging.error("页面跳转失败，达到最大重试次数，退出")
            driver.quit()
            exit()
        time.sleep(3)  # ⏳ 等待 3 秒后再尝试

# **等待搜索结果页面加载**
retry_count = 0
while retry_count < max_retries:
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "loadedmonth"))
        )
        logging.info("月份信息加载成功")
        break  # ✅ 成功，跳出循环
    except TimeoutException:
        retry_count += 1
        logging.error(f"月份信息加载失败，正在重试 ({retry_count}/{max_retries})")
        if retry_count == max_retries:
            logging.error("月份信息加载失败，达到最大重试次数，退出")
            driver.quit()
            exit()
        time.sleep(3)  # ⏳ 等待 3 秒后再尝试

# 1️⃣2️⃣ **点击折叠按钮，智能等待加载完成**
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
        break  # ✅ 成功，跳出循环
    except TimeoutException:
        retry_count += 1
        logging.error(f"月份信息展开失败，正在重试 ({retry_count}/{max_retries})")
        if retry_count == max_retries:
            logging.error("月份信息展开失败，达到最大重试次数，退出")
            driver.quit()
            exit()
        time.sleep(3)  # ⏳ 等待 3 秒后再尝试
    except NoSuchElementException:
        logging.warning("找不到展开按钮，可能已经展开")
        break  # ✅ 可能已经展开，跳出循环

# **获取当前 HTML 页面**
html_before_click = driver.execute_script("return document.body.outerHTML;")

# ✅ **使用正则表达式提取可预约的日期**
available_dates = []
partially_available_dates = []

pattern = re.compile(r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?<img[^>]*?alt="(全て空き|一部空き)"', re.S)

for match in pattern.finditer(html_before_click):
    date_number = match.group(1)
    status = match.group(2)

    if status == "全て空き":
        available_dates.append(date_number)
    elif status == "一部空き":
        partially_available_dates.append(date_number)


logging.info(f"可预约的日期（完全空闲）：{available_dates}")
logging.info(f"可预约的日期（部分空闲）：{partially_available_dates}")

"""
# 🎌 **过滤掉非休日 & 非祝日的日期**
def is_holiday_or_weekend(date_str):
    """检查日期是否为日本的周六、周日或祝日"""
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)

available_dates = [date for date in available_dates if is_holiday_or_weekend(date)]
partially_available_dates = [date for date in partially_available_dates if is_holiday_or_weekend(date)]

logging.info(f"可预约的日期（完全空闲，仅休日&祝日）：{available_dates}")
logging.info(f"可预约的日期（部分空闲，仅休日&祝日）：{partially_available_dates}")
"""
# **存储所有空位信息**
availability_info = {}

# 1️⃣4️⃣ **点击可预约的日期**
for date in available_dates + partially_available_dates:
    logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")

    try:
        date_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, f"month_{date}"))
        )
        date_element.click()
        logging.info(f"成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

        # ✅ **等待 `week-info` 确保时间段已加载**
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "week-info"))
        )
        logging.info(f"{date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

        # **获取最新 HTML**
        time.sleep(10)  # **短暂等待 JS 渲染**
        html_after_click = driver.execute_script("return document.body.outerHTML;")

        # **先清理当前日期的旧数据，防止错误数据残留**
        availability_info = {k: v for k, v in availability_info.items() if k[0] != date}

        # **解析新数据**
        pattern_slots = re.compile(
            r'<input id="A_(\d{8})_(\d{2})" type="hidden" value="(\d+)">',
            re.S
        )

        for match in pattern_slots.finditer(html_after_click):
            slot_date, slot_suffix, available_count = match.groups()

            # **只存入当前点击的日期，不存入其他日期**
            if slot_date == date:
                slot_time = {
                    "10": "7-9点", "20": "9-11点", "30": "11-13点",
                    "40": "13-15点", "50": "15-17点", "60": "17-19点", "70": "19-21点"
                }.get(slot_suffix, "未知时间段")

                availability_info[(slot_date, slot_time)] = available_count

    except TimeoutException:
        logging.error(f"无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

# **最终汇总**
logging.info("所有可预约时间段:")
for (date, time_slot), count in availability_info.items():
    logging.info(f"{date} | {time_slot} | 可预约：{count} 人")

driver.quit()











import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 📩 **邮件发送函数**
def send_email(subject, body):
    sender_email = os.getenv("sender_email") # 你的 Gmail 地址
    receiver_email = os.getenv("receiver_email").split(",") # 收件人邮箱
    password = os.getenv("password")# Gmail 应用专用密码

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_email)  # ✅ 解决 encode 错误
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        logging.info("📧 邮件发送成功")
    except Exception as e:
        logging.error(f"❌ 邮件发送失败: {e}")

# 📂 **读取上次的预约信息**
last_file = "last_availability_toneri.txt"
if os.path.exists(last_file):
    with open(last_file, "r", encoding="utf-8") as f:
        last_availability_toneri = f.read()
else:
    last_availability_toneri = ""

# 📌 **按照 日期 和 时间 进行排序**
time_order = {
    "7-9点": 1, "9-11点": 2, "11-13点": 3,
    "13-15点": 4, "15-17点": 5, "17-19点": 6, "19-21点": 7
}

sorted_availability = sorted(
    availability_info.items(),
    key=lambda x: (x[0][0], time_order.get(x[0][1], 99))  # 先按日期排序，再按时间排序
)

from datetime import datetime

# 📌 **定义曜日映射**
weekday_japanese = ["月", "火", "水", "木", "金", "土", "日"]

# 📝 **当前预约信息（排序后，带星期）**
current_availability = "\n".join([
    f"{date[:4]}-{date[4:6]}-{date[6:]} ({weekday_japanese[datetime.strptime(date, '%Y%m%d').weekday()]}) | {time_slot} | 可预约：{count} 人"
    for (date, time_slot), count in sorted_availability
])

# 📌 **比较新旧数据**
if current_availability.strip() != last_availability_toneri.strip():
    logging.info("🔔 预约信息发生变化，发送邮件通知")
    
    # **📩 发送邮件**
    email_subject = "🏸 舍人-网球场预约更新通知"
    email_body = "本次查询到的可预约时间如下：\n\n" + current_availability
    send_email(email_subject, email_body)

    # **📂 更新 `last_availability_toneri.txt`**
    with open(last_file, "w", encoding="utf-8") as f:
        f.write(current_availability)
else:
    logging.info("✅ 预约信息无变化，不发送邮件")
