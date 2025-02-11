import re
import time
import random
import logging
from datetime import datetime
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
from bs4 import BeautifulSoup
load_dotenv("/root/tenniscourt/config.env", override=True)
time.sleep(random.uniform(1, 30))  # 等待随机秒数

# 配置日志输出到文件
logging.basicConfig(
    filename="tennis_okubo.log",  # 日志文件名
    level=logging.INFO,             # 记录 INFO 及以上级别的日志
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 1️⃣ 配置 Selenium
options = Options()
options.add_argument("--headless")  # 无头模式运行
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 2️⃣ 访问主页并确保加载成功
url = "https://user.shinjuku-shisetsu-yoyaku.jp/regasu/reserve/gin_menu"
while True:
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "contents"))
        )
        logging.info("主页加载成功")
        break
    except TimeoutException:
        logging.warning("主页加载超时，正在刷新...")
time.sleep(random.uniform(1, 3))
logging.info("搜索按钮加载成功")

# 3️⃣ 依次点击页面中的各个按钮或链接

# 点击“かんたん操作”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @alt='かんたん操作']"))
    )
    image_button.click()
    logging.info("已点击按钮 'かんたん操作'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（かんたん操作按钮）：%s", e)

# 点击“空き状況確認”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @alt='空き状況確認']"))
    )
    image_button.click()
    logging.info("已点击按钮 '空き状況確認'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（空き状況確認按钮）：%s", e)

# 点击 id 为 "button3" 的链接
try:
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "button3"))
    )
    link_button.click()
    logging.info("已点击链接按钮 'button3'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（button3）：%s", e)

# 点击 id 为 "id0" 的链接
try:
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "id0"))
    )
    link_button.click()
    logging.info("已点击链接按钮 'id0'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（id0）：%s", e)

# 点击 id 为 "button0" 的链接
try:
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "button0"))
    )
    link_button.click()
    logging.info("已点击链接按钮 'button0'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（button0）：%s", e)

# 点击 title 为 "テニス" 的链接
try:
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='テニス']"))
    )
    link_button.click()
    logging.info("已点击链接按钮 'テニス'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
except Exception as e:
    logging.exception("操作失败（テニス链接）：%s", e)

# 选择所有复选框并点击“確定”按钮（选择一天空位）
try:
    checkboxes = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//input[@type='checkbox' and @name='chkbox']"))
    )
    for checkbox in checkboxes:
        if not checkbox.is_selected():
            checkbox.click()
    logging.info("已选中所有的曜日复选框（日、月、火、水、木、金、土、祝日）")
    
    ok_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "btnOK"))
    )
    ok_button.click()
    logging.info("已点击確定按钮，跳转至新页面 一天空位")

except Exception as e:
    logging.exception("第一阶段操作失败：%s", e)

# 点击嵌入 <a> 标签中含有 <img> alt="施設別に切替" 的链接，进入一周空位页面
try:
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[img[@alt='施設別に切替']]"))
    )
    link_button.click()
    logging.info("已点击链接按钮 '施設別に切替'，进入新页面 一周空位")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[@alt='日付別に切替']"))
    )
    logging.info("新页面加载完成，找到了 alt 为 '日付別に切替' 的元素。")
    new_page_html = driver.page_source
except Exception as e:
    logging.exception("第二阶段操作失败：%s", e)

# 4️⃣ 使用 BeautifulSoup 解析页面中显示一周空位的表格信息
try:
    soup = BeautifulSoup(new_page_html, "html.parser")
    # 从 <thead> 中提取时间段信息（第一个<th>为空，其余依次为各个时间段）
    header_ths = soup.find("thead").find_all("th")
    time_slots = []
    for th in header_ths[1:]:
        text = th.get_text(separator=" ", strip=True)
        time_slots.append(text)

    availability_info = []
    # 遍历所有 <tbody> 中的行
    for tbody in soup.find_all("tbody"):
        tr = tbody.find("tr")
        if not tr:
            continue
        th_date = tr.find("th")
        if not th_date:
            continue
        date_text = th_date.get_text(strip=True)
        # 提取 m/d 格式的日期，如 "2/13"
        match = re.search(r"(\d+/\d+)", date_text)
        date_str = match.group(1) if match else date_text

        tds = tr.find_all("td")
        for i, td in enumerate(tds):
            img = td.find("img")
            # 当图片 alt 为 "O" 时表示该时间段有空位
            if img and img.get("alt") == "O":
                time_slot = time_slots[i] if i < len(time_slots) else "未知"
                availability_info.append({"date": date_str, "time": time_slot})

    # 定义辅助函数用于排序
    def parse_date(date_str):
        try:
            return datetime.strptime("2023/" + date_str, "%Y/%m/%d")
        except Exception:
            return datetime.max

    def parse_time_slot(time_str):
        match = re.search(r"(\d{2}:\d{2})", time_str)
        return match.group(1) if match else time_str

    # 先按日期，再按时间段起始时间排序
    availability_info.sort(key=lambda v: (parse_date(v["date"]), parse_time_slot(v["time"])))

    for v in availability_info:
        logging.info("空位信息 - 日期: %s, 时间段: %s", v["date"], v["time"])
except Exception as e:
    logging.exception("解析空位信息失败：%s", e)

driver.quit()







import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender_email = os.getenv("sender_email2") # 你的 Gmail 地址
receiver_email = os.getenv("receiver_email").split(",") # 收件人邮箱
password = os.getenv("password2")# Gmail 应用专用密码
# 📩 **邮件发送函数**
def send_email(subject, body):


    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg['To'] = "<noreply@example.com>"
    msg["Subject"] = subject
    msg['Bcc'] = ', '.join(receiver_email) if isinstance(receiver_email, list) else receiver_email

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

# 📂 读取上次的预约信息
last_file = "last_availability_okubo.txt"
if os.path.exists(last_file):
    with open(last_file, "r", encoding="utf-8") as f:
        last_availability_okubo = f.read().strip()
else:
    last_availability_okubo = ""

# 📌 定义曜日映射
weekday_japanese = ["水", "木", "金", "土", "日", "月", "火"]

# 📝 **当前预约信息（排序后，带星期）**
current_availability = "\n".join([
    f"{entry['date']} ({weekday_japanese[datetime.strptime(entry['date'], '%m/%d').weekday()]}) | {entry['time']} | 可预约"
    for entry in availability_info
])

# **确保 current_availability 不是空的**
if current_availability:
    # 📌 **比较新旧数据**
    if current_availability.strip() != last_availability_okubo.strip():
        logging.info("🔔 预约信息发生变化，发送邮件通知")
        
        # **📩 发送邮件**
        email_subject = "🏸 大久保-网球场预约更新通知"
        email_body = "本次查询到的可预约时间如下：\n\n" + current_availability
        send_email(email_subject, email_body)

        # **📂 更新 `last_availability_okubo.txt`**
        with open(last_file, "w", encoding="utf-8") as f:
            f.write(current_availability)
    else:
        logging.info("✅ 预约信息无变化，不发送邮件")
else:
    logging.warning("❌ 没有找到新的可预约时间，文件不会被更新")
