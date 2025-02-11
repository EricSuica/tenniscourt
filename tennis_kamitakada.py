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
load_dotenv("/root/tenniscourt/config.env", override = True)
time.sleep(random.uniform(1, 30))  # 等待随机秒数

# 配置日志输出到文件
logging.basicConfig(
    filename="tennis_kamitakada.log",  # 日志文件名
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
url = "https://yoyaku.nakano-tokyo.jp/stagia/reserve/grb_init"
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

# 点击“空き状況確認”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and contains(@src, 'btn_check_status_01.gif')]"))
    )
    image_button.click()
    logging.info("已点击按钮 '空き状況確認'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "allChecked")))
except Exception as e:
    logging.exception("操作失败（空き状況確認按钮）：%s", e)



#分類選択1

try:

    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "allChecked"))
    )
    link_button.click()
    logging.info("已点击链接按钮 '全て'")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@id='allChecked' and contains(@class, 'active')]"))
    )

    logging.info("点击成功，按钮已变为 'active' 状态")
except Exception as e:
    logging.exception("操作失败(allChecked):%s", e)


# 点击“确定”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]"))
    )
    image_button.click()
    logging.info("已点击按钮 '確定'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "button2")))

except Exception as e:
    logging.exception("操作失败（確定）：%s", e)


#分類選択２


try:
    # 等待并点击 id="button2" 的链接
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "button2"))
    )
    link_button.click()
    logging.info("已点击链接按钮 '運動施設'")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@id='button2' and contains(@class, 'active')]"))
    )

    logging.info("点击成功，按钮已变为 'active' 状态")
except Exception as e:
    logging.exception("操作失败（運動施設）：%s", e)

# 点击“确定”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]"))
    )
    image_button.click()
    logging.info("已点击按钮 '確定'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-page-next.gif')]")))
except Exception as e:
    logging.exception("操作失败（確定）：%s", e)



#目的選択

try:
    # 等待并点击 id="次頁" 的链接
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nextButton"))
    )
    link_button.click()
    logging.info("已点击链接按钮 '次頁'")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '硬式テニス')]"))
    )

    logging.info("已出现 硬式テニス")
except Exception as e:
    logging.exception("操作失败（次頁）：%s", e)




# 点击“硬式テニス”按钮

try:
    # 等待并点击 "硬式テニス" 的链接
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '硬式テニス')]"))
    )
    link_button.click()
    logging.info("已点击链接按钮 '硬式テニス'")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "id0"))
    )

    logging.info("已出现 上高田運動施設")
except Exception as e:
    logging.exception("操作失败（硬式テニス）：%s", e)




# 点击“上高田運動施設”按钮

try:
    # 等待并点击 id="button2" 的链接
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "id1"))
    )
    link_button.click()
    logging.info("已点击按钮 '上高田運動施設'，进入新页面")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@id='id1' and contains(@class, 'active')]"))
    )

    logging.info("点击成功，按钮已变为 'active' 状态")
except Exception as e:
    logging.exception("操作失败（上高田運動施設）：%s", e)

# 点击“确定”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "btnOk"))
    )
    image_button.click()
    logging.info("已点击按钮 '確定'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "button0")))
    logging.info("已出现 庭球場第１コート")

except Exception as e:
    logging.exception("操作失败（確定）：%s", e)



# 点击“全て”按钮

try:
    # 等待并点击 id="button2" 的链接
    link_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "allChecked"))
    )
    link_button.click()
    logging.info("已点击按钮 '全て'")

    # **等待 class 变化，确保点击成功**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@id='allChecked' and contains(@class, 'active')]"))
    )

    logging.info("点击成功，按钮已变为 'active' 状态")
except Exception as e:
    logging.exception("操作失败（全て）：%s", e)



# 点击“确定”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]"))
    )
    image_button.click()
    logging.info("已点击按钮 '確定'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "filter-by-day")))
    logging.info("已出现 曜日を絞る")

except Exception as e:
    logging.exception("操作失败（確定）：%s", e)




#表示開始日選択


# 点击日期

from datetime import datetime  # 修正导入
try:
    # 获取今天的日期（格式：YYYYMMDD）
    today_date = datetime.today().strftime("%Y%m%d")  # 修正这里
    logging.info(f"今天的日期是：{today_date}")
    
    # 构造动态的 XPath 来匹配 `onclick="dateClick(..., YYYYMMDD)"`
    date_xpath = f"//td[contains(@onclick, 'dateClick') and contains(@onclick, '{today_date}')]"

    # 等待并点击今天的日期按钮
    date_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, date_xpath))
    )
    date_button.click()
    logging.info(f"已点击今天的日期按钮（{today_date})")

    # **等待 class 变为 'active'**
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"{date_xpath}[contains(@class, 'active')]"))
    )

    logging.info(f"日期按钮（{today_date}）已变为 active 状态")

except Exception as e:
    logging.exception("操作失败（日期选择）：%s", e)



#点击星期

try:
    # 遍历 id="img0" 到 id="img7"
    for i in range(8):
        img_id = f"img{i}"
        logging.info(f"尝试点击 {img_id}")

        # 等待元素可点击
        img_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, img_id))
        )

        # 点击元素
        img_element.click()
        logging.info(f"已点击 {img_id}")

        # 可选：等待页面变化，确保点击生效（如果页面有明显变化）
        time.sleep(1)  # 等待 1 秒，避免连续点击过快

except Exception as e:
    logging.exception("操作失败（点击 img0 - img7):%s", e)



# 点击“确定”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-ok.gif')]"))
    )
    image_button.click()
    logging.info("已点击按钮 '確定'，进入新页面")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, '/stagia/jsp/images_jp/common/btn-nav-change.gif')]")))
    logging.info("已出现 一周时间表示按钮")

except Exception as e:
    logging.exception("操作失败（確定）：%s", e)



from selenium.common.exceptions import  TimeoutException, ElementNotInteractableException

# 解析 HTML

import os
import smtplib
import logging
import re
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium.common.exceptions import ElementNotInteractableException
from bs4 import BeautifulSoup

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# WebDriver 解析页面
all_available_slots = []

while True:  # 循环直到无法翻页
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 获取当前日期
    today_date_element = soup.select_one("li.day#li")
    if today_date_element:
        raw_date = today_date_element.get_text(strip=True)  # 例如 "令和07年2月8日(土)"

        # 使用正则提取和转换日期
        match = re.search(r"令和(\d+)年(\d+)月(\d+)日", raw_date)
        if match:
            reiwa_year, month, day = map(int, match.groups())
            western_year = 2018 + reiwa_year  # 令和元年(2019)是西历2019
            today_date = f"{western_year}-{month:02d}-{day:02d}"  # YYYY-MM-DD
        else:
            today_date = "未知日期"

    logging.info(today_date)  # 输出格式化的日期，例如：2025-02-08

    # 提取设施名称
    facilities = [row.get_text(strip=True) for row in soup.select("tbody tr th strong")]

    # 提取时间段
    time_slots = [header.get_text(strip=True).replace("～", "-") for header in soup.select("thead tr th[id^='td10_']")]

    # 提取空位信息
    facility_rows = soup.select("tbody tr")

    for facility_index, row in enumerate(facility_rows):
        if facility_index >= len(facilities):
            continue  # 防止索引超出范围
        facility_name = facilities[facility_index]
        cells = row.select("td[id^='td11_'], td[id^='td12_'], td[id^='td13_'], td[id^='td14_'], td[id^='td15_'], td[id^='td16_']")

        for time_index, cell in enumerate(cells):
            img = cell.find("img")
            if img and any(keyword in img["src"] for keyword in ["icon_timetable_sankaku.gif", "icon_timetable_O.gif"]):
                all_available_slots.append({
                    "date": today_date,  # **使用英文键**
                    "facility": facility_name,
                    "time": time_slots[time_index]
                })


    # 尝试点击 "次へ" 按钮进入下一天
    try:
        next_button = driver.find_element("xpath", "//img[@alt='次へ']")
        next_button.click()
        time.sleep(1)  # 等待页面加载
    except ElementNotInteractableException:
        logging.info("已到达最后一天，停止获取。")
        break
import jpholiday

# 筛选符合条件的预约信息
partial_available_slots = []

for slot in all_available_slots:
    date_str = slot["date"]  # 格式为 YYYY-MM-DD
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = date_obj.weekday()  # 0=Monday, ..., 6=Sunday
    time_range = slot["time"]

    # 判断是否为祝休日（包括周六、周日）
    is_holiday = jpholiday.is_holiday(date_obj) or weekday in [5, 6]  # 周六 (5) / 周日 (6) 也是祝休日

    # 平日筛选 19:00-21:00
    if not is_holiday and time_range in ["19:00-20:00", "20:00-21:00"]:
        partial_available_slots.append(slot)

    # 祝休日保留所有时段
    if is_holiday:
        partial_available_slots.append(slot)

# 打印筛选后的可预约时间
logging.info("🎾 筛选后的部分空位信息（partial_available_slots）：")
for slot in partial_available_slots:
    logging.info(f"{slot['date']} | {slot['facility']} | {slot['time']}")
    
# 📂 读取上次的预约信息
LAST_FILE = "last_availability_kamitakada.txt"
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_availability_kamitakada = f.read().strip()
else:
    last_availability_kamitakada = ""

# **定义曜日映射**
WEEKDAY_JAPANESE = ["月", "火", "水", "木", "金", "土", "日"]

# 🏸 **处理预约数据**
if partial_available_slots:
    # 格式化当前预约信息（带星期）
    current_availability = "\n".join([
        f"{entry['date']} ({WEEKDAY_JAPANESE[datetime.strptime(entry['date'], '%Y-%m-%d').weekday()]}) | {entry['time']} | 可预约"
        for entry in partial_available_slots
    ])

    # 📌 比较新旧数据
    if current_availability.strip() != last_availability_kamitakada.strip():
        logging.info("🔔 预约信息发生变化，发送邮件通知")

        # **📩 发送邮件**
        def send_email(subject, body):
            sender_email = os.getenv("sender_email2") # 你的 Gmail 地址
            receiver_email = os.getenv("receiver_email").split(",") # 收件人邮箱
            password = os.getenv("password2")# Gmail 应用专用密码

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = "<noreply@example.com>"
            msg["Subject"] = subject
            msg["Bcc"] = ', '.join(receiver_email) if isinstance(receiver_email, list) else receiver_email
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

        email_subject = "🏸 上高田-网球场预约更新通知"
        email_body = "本次查询到的可预约时间如下：\n\n" + current_availability
        send_email(email_subject, email_body)

        # 📂 更新 `last_availability_kamitakada.txt`
        with open(LAST_FILE, "w", encoding="utf-8") as f:
            f.write(current_availability)

    else:
        logging.info("✅ 预约信息无变化，不发送邮件")
else:
    logging.warning("❌ 未找到任何可预约信息")

# 关闭 WebDriver
driver.quit()
