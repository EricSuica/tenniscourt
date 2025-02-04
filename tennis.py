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

# 设置日志
logging.basicConfig(
    filename="scraper.log",  # 输出到文件
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
sport_select.select_by_value("1000_1020")  # "テニス（ハード）"
logging.info("種目选择成功")

# 6️⃣ **等待 JavaScript 更新公园选项**
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//select[@id='bname-home']/option[@value='1350']"))
)
logging.info("公园选项加载成功")

# 7️⃣ 选择 公園（选择 "有明テニスＡ屋外ハードコート"）
park_select = Select(driver.find_element(By.ID, "bname-home"))
park_select.select_by_value("1350")
logging.info("公园选择成功")

# 8️⃣ **点击搜索按钮**
search_button = driver.find_element(By.ID, "btn-go")
search_button.click()
logging.info("搜索按钮点击成功")

# **等待 URL 变化**
try:
    WebDriverWait(driver, 20).until(lambda driver: driver.current_url != url)
    logging.info("页面跳转成功")
except TimeoutException:
    logging.error("页面跳转超时")
    driver.quit()
    exit()

# **等待搜索结果页面加载**
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "loadedmonth"))
    )
    logging.info("月份信息加载成功")
except TimeoutException:
    logging.error("月份信息加载失败")
    driver.quit()
    exit()

# 1️⃣2️⃣ **点击折叠按钮，智能等待加载完成**
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
except TimeoutException:
    logging.error("月份信息展开失败")
    driver.quit()
    exit()
except NoSuchElementException:
    logging.warning("找不到展开按钮，可能已经展开")

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
        time.sleep(5)  # **短暂等待 JS 渲染**
        html_after_click = driver.execute_script("return document.body.outerHTML;")

        # **解析新数据**
        pattern_slots = re.compile(r'<td id="(\d{8}_\d{2})".*?<img[^>]*?alt="空き".*?<span>(\d+)</span>', re.S)

        for match in pattern_slots.finditer(html_after_click):
            full_slot_id = match.group(1)
            slot_date, slot_suffix = full_slot_id.split("_")
            slot_time = {
                "10": "7-9点", "20": "9-11点", "30": "11-13点",
                "40": "13-15点", "50": "15-17点", "60": "17-19点", "70": "19-21点"
            }[slot_suffix]
            available_count = match.group(2)
            availability_info[(slot_date, slot_time)] = available_count

    except TimeoutException:
        logging.error(f"无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

# **最终汇总**
logging.info("所有可预约时间段:")
for (date, time_slot), count in availability_info.items():
    logging.info(f"{date} | {time_slot} | 可预约：{count} 人")

driver.quit()
