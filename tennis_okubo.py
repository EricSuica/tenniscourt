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
from selenium.common.exceptions import StaleElementReferenceException

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

# **存储所有空位信息**
availability_info = {}

# 访问主页并确保加载成功
url = "https://www.shinjuku.eprs.jp/regasu/web/"
while True:
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "btn-go"))
        )
        logging.info("主页加载成功")
        break  # 成功加载主页且不是休止日，跳出循环
    except TimeoutException:
        logging.warning("主页加载超时，正在刷新...")

time.sleep(random.uniform(1, 3))
logging.info("搜索按钮加载成功")


# 3️⃣ 依次点击页面中的各个按钮或链接
# 点击“1か月”按钮
try:
    one_month_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//label[@class='btn radiobtn' and @for='thismonth']"))
    )
    one_month_button.click()
    logging.info("已点击按钮 '1か月'")
except Exception as e:
    logging.exception("操作失败(1か月按钮):%s", e)

# “选择大久保スポーツプラザ（庭球場）”
try:
    # 等待 select 元素加载
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "bname"))
    )

    # 创建 Select 对象
    select = Select(select_element)

    # 选择 "大久保スポーツプラザ（庭球場）"
    select.select_by_visible_text("大久保スポーツプラザ（庭球場）")

    logging.info("已选择 '大久保スポーツプラザ（庭球場）'")
    
    # 等待页面更新
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element(
            (By.XPATH, "//div[@id='searchCondition']/span"),
            "大久保スポーツプラザ（庭球場）"
        )
    )
except Exception as e:
    logging.exception("操作失败（选择 '大久保スポーツプラザ（庭球場）'):%s", e)


# 点击“搜索“按钮
try:
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "btn-go"))
    )
    search_button.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "week-info")))
    logging.info("已点击按钮 '搜索',并进入新页面，并成功获取周空位信息")
except Exception as e:
    logging.exception("操作失败(搜索):%s", e)

# 点击“月表示“按钮
try:
    # 等待并点击 "月表示" 按钮
    monthly_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-light' and @data-target='#monthly']"))
    )
    monthly_button.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loadedmonth")))
    logging.info("已点击 '月表示' 按钮，并成功获取月份信息")

except Exception as e:
    logging.exception("点击 '月表示' 按钮失败：%s", e)


# “已选择 '庭球場 １面' (value=10250080)”

try:
    # 等待 select 元素加载
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "facility-select"))
    )

    # 创建 Select 对象
    select = Select(select_element)

    # 选择 value="10250080"
    select.select_by_value("10250080")
    time.sleep(2)  # **短暂等待 JS 渲染**

    logging.info("已选择 '庭球場 １面' (value=10250080)")

    # 等待选项生效（可根据页面逻辑调整）

except Exception as e:
    logging.exception("操作失败（选择 '庭球場 １面(value=10250080)'）: %s", e)


# **获取当前 HTML 页面**
html_current = driver.execute_script("return document.body.outerHTML;")
month_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "month-head")))
# 获取 `month-head` 的文本
month_text = month_element.text

# ✅ **使用正则表达式提取当月可预约的日期**
available_dates = []
partially_available_dates = []

pattern = re.compile(r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?<img[^>]*?alt="(全て空き|一部空き)"', re.S)

for match in pattern.finditer(html_current):
    date_number = match.group(1)
    status = match.group(2)

    if status == "全て空き":
        available_dates.append(date_number)
    elif status == "一部空き":
        partially_available_dates.append(date_number)



logging.info(f"{month_text}可预约的日期（完全空闲）：{available_dates}")
logging.info(f"{month_text}可预约的日期（部分空闲）：{partially_available_dates}")

"""
# 🎌 **过滤掉非休日 & 非祝日的日期**
def is_holiday_or_weekend(date_str):
    #检查日期是否为日本的周六、周日或祝日
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)

available_dates = [date for date in available_dates if is_holiday_or_weekend(date)]
partially_available_dates = [date for date in partially_available_dates if is_holiday_or_weekend(date)]

logging.info(f"{month_text}可预约的日期（完全空闲，仅休日&祝日）：{available_dates}")
logging.info(f"{month_text}可预约的日期（部分空闲，仅休日&祝日）：{partially_available_dates}")

"""

    




# 1️⃣4️⃣ **点击可预约的日期**
for date in available_dates + partially_available_dates:
    logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")

    attempt = 0
    max_attempts = 3  # 允许最多重试 3 次

    while attempt < max_attempts:
        try:
            attempt += 1
            logging.info(f"🔄 尝试第 {attempt} 次点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

            # 重新获取元素，确保元素有效
            date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"month_{date}"))
            )

            date_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, f"month_{date}"))
            )
            date_element.click()
            logging.info(f"✅ 成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            time.sleep(2)  # **短暂等待 JS 渲染**
            
            # ✅ **等待 `week-info` 确保时间段已加载**
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "week-info"))
            )
            logging.info(f"✅ {date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

            # **获取最新 HTML**
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
                        "10": "9:00-11:30", "20": "11:30-13:30",
                        "30": "13:30-15:30", "40": "15:30-17:30",
                        "50": "17:30-19:30", "60": "19:30-22:00"
                    }.get(slot_suffix, "未知时间段")

                    availability_info[(slot_date, slot_time)] = available_count

            break  # 成功后退出循环

        except StaleElementReferenceException:
            logging.warning(f"⚠️ 目标元素失效，第 {attempt} 次重试 {date[:4]}年{date[4:6]}月{date[6:]}日...")
            time.sleep(1)  # 短暂等待，避免频繁请求

        except TimeoutException:
            logging.error(f"❌ 无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            driver.quit()
            exit(0)  # 终止程序


# 点击“下月”按钮
try:
    next_month_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "next-month"))
    )

    # 使用 JavaScript 直接点击按钮
    driver.execute_script("arguments[0].click();", next_month_button)
    logging.info("已点击按钮 '下月'，进入新页面")
    time.sleep(3)  # **短暂等待 JS 渲染**

    month_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "month-head")))
    # 获取 `month-head` 的文本
    month_text = month_element.text

    # 记录日志
    logging.info(f"✅ 已出现 下月信息: {month_text}")

except Exception as e:
    logging.exception("操作失败（下月）：%s", e)

# **获取下月 HTML 页面**
html_next_month = driver.execute_script("return document.body.outerHTML;")

# **正则表达式匹配 下月可预约的日期**
pattern = re.compile(r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?<img[^>]*?alt="(全て空き|一部空き|予約あり)"', re.S)

# **使用正则表达式提取下月可预约的日期**
matches = list(pattern.finditer(html_next_month))  # 先把匹配项存入列表

available_dates = []
partially_available_dates = []

if not matches:  # 如果 `matches` 为空
    logging.info(f"⚠️ {month_text} 空位未开放查询")
else:
    for match in matches:
        date_number = match.group(1)
        status = match.group(2)

        if status == "全て空き":
            available_dates.append(date_number)
        elif status == "一部空き":
            partially_available_dates.append(date_number)

if available_dates != []:
    logging.info(f"{month_text}可预约的日期（完全空闲）：{available_dates}")
    logging.info(f"{month_text}可预约的日期（部分空闲）：{partially_available_dates}")
    
    """
    # 🎌 **过滤掉非休日 & 非祝日的日期**
    def is_holiday_or_weekend(date_str):
        #检查日期是否为日本的周六、周日或祝日
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)
    
    available_dates = [date for date in available_dates if is_holiday_or_weekend(date)]
    partially_available_dates = [date for date in partially_available_dates if is_holiday_or_weekend(date)]
    
    logging.info(f"{month_text}可预约的日期（完全空闲，仅休日&祝日）：{available_dates}")
    logging.info(f"{month_text}可预约的日期（部分空闲，仅休日&祝日）：{partially_available_dates}")
    """
    
    
    
    # 1️⃣4️⃣ **点击可预约的日期**
    for date in available_dates + partially_available_dates:
        logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")

        attempt = 0
        max_attempts = 3  # 允许最多重试 3 次

        while attempt < max_attempts:
            try:
                attempt += 1
                logging.info(f"🔄 尝试第 {attempt} 次点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

                # 重新获取元素，确保元素有效
                date_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, f"month_{date}"))
                )

                date_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, f"month_{date}"))
                )
                date_element.click()
                logging.info(f"✅ 成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
                time.sleep(2)  # **短暂等待 JS 渲染**
                
                # ✅ **等待 `week-info` 确保时间段已加载**
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "week-info"))
                )
                logging.info(f"✅ {date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

                # **获取最新 HTML**
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
                            "10": "9:00-11:30", "20": "11:30-13:30",
                            "30": "13:30-15:30", "40": "15:30-17:30",
                            "50": "17:30-19:30", "60": "19:30-22:00"
                        }.get(slot_suffix, "未知时间段")

                        availability_info[(slot_date, slot_time)] = available_count

                break  # 成功后退出循环

            except StaleElementReferenceException:
                logging.warning(f"⚠️ 目标元素失效，第 {attempt} 次重试 {date[:4]}年{date[4:6]}月{date[6:]}日...")
                time.sleep(1)  # 短暂等待，避免频繁请求

            except TimeoutException:
                logging.error(f"❌ 无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
                driver.quit()
                exit(0)  # 终止程序


# 点击“前月”按钮
try:
    image_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "last-month"))
    )
    image_button.click()
    logging.info("已点击按钮 '前月'，进入新页面")
    time.sleep(3)  # **短暂等待 JS 渲染**

    month_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "month-head")))
    # 获取 `month-head` 的文本
    month_text = month_element.text

    # 记录日志
    logging.info(f"✅ 已出现 前月信息: {month_text}")

except Exception as e:
    logging.exception("操作失败（前月）：%s", e)



# “已选择 '庭球場 １面' (value=10250090)”

try:
    # 等待 select 元素加载
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "facility-select"))
    )

    # 创建 Select 对象
    select = Select(select_element)

    # 选择 value="10250080"
    select.select_by_value("10250090")
    time.sleep(2)  # **短暂等待 JS 渲染**

    logging.info("已选择 '庭球場 １面' (value=10250090)")

    # 等待选项生效（可根据页面逻辑调整）

except Exception as e:
    logging.exception("操作失败（选择 '庭球場 １面(value=10250090)'）: %s", e)


# **获取当前 HTML 页面**
html_current = driver.execute_script("return document.body.outerHTML;")
month_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "month-head")))
# 获取 `month-head` 的文本
month_text = month_element.text

# ✅ **使用正则表达式提取当月可预约的日期**
available_dates = []
partially_available_dates = []

pattern = re.compile(r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?<img[^>]*?alt="(全て空き|一部空き)"', re.S)

for match in pattern.finditer(html_current):
    date_number = match.group(1)
    status = match.group(2)

    if status == "全て空き":
        available_dates.append(date_number)
    elif status == "一部空き":
        partially_available_dates.append(date_number)



logging.info(f"{month_text}可预约的日期（完全空闲）：{available_dates}")
logging.info(f"{month_text}可预约的日期（部分空闲）：{partially_available_dates}")

"""
# 🎌 **过滤掉非休日 & 非祝日的日期**
def is_holiday_or_weekend(date_str):
    #检查日期是否为日本的周六、周日或祝日
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)

available_dates = [date for date in available_dates if is_holiday_or_weekend(date)]
partially_available_dates = [date for date in partially_available_dates if is_holiday_or_weekend(date)]

logging.info(f"{month_text}可预约的日期（完全空闲，仅休日&祝日）：{available_dates}")
logging.info(f"{month_text}可预约的日期（部分空闲，仅休日&祝日）：{partially_available_dates}")

"""

    




# 1️⃣4️⃣ **点击可预约的日期**
for date in available_dates + partially_available_dates:
    logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")

    attempt = 0
    max_attempts = 3  # 允许最多重试 3 次

    while attempt < max_attempts:
        try:
            attempt += 1
            logging.info(f"🔄 尝试第 {attempt} 次点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

            # 重新获取元素，确保元素有效
            date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"month_{date}"))
            )

            date_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, f"month_{date}"))
            )
            date_element.click()
            logging.info(f"✅ 成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            time.sleep(2)  # **短暂等待 JS 渲染**
            
            # ✅ **等待 `week-info` 确保时间段已加载**
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "week-info"))
            )
            logging.info(f"✅ {date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

            # **获取最新 HTML**
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
                        "10": "9:00-11:30", "20": "11:30-13:30",
                        "30": "13:30-15:30", "40": "15:30-17:30",
                        "50": "17:30-19:30", "60": "19:30-22:00"
                    }.get(slot_suffix, "未知时间段")

                    availability_info[(slot_date, slot_time)] = available_count

            break  # 成功后退出循环

        except StaleElementReferenceException:
            logging.warning(f"⚠️ 目标元素失效，第 {attempt} 次重试 {date[:4]}年{date[4:6]}月{date[6:]}日...")
            time.sleep(1)  # 短暂等待，避免频繁请求

        except TimeoutException:
            logging.error(f"❌ 无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
            driver.quit()
            exit(0)  # 终止程序


# 点击“下月”按钮
try:
    next_month_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "next-month"))
    )

    # 使用 JavaScript 直接点击按钮
    driver.execute_script("arguments[0].click();", next_month_button)
    logging.info("已点击按钮 '下月'，进入新页面")
    time.sleep(3)  # **短暂等待 JS 渲染**

    month_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "month-head")))
    # 获取 `month-head` 的文本
    month_text = month_element.text

    # 记录日志
    logging.info(f"✅ 已出现 下月信息: {month_text}")

except Exception as e:
    logging.exception("操作失败（下月）：%s", e)

# **获取下月 HTML 页面**
html_next_month = driver.execute_script("return document.body.outerHTML;")

# **正则表达式匹配 下月可预约的日期**
pattern = re.compile(r'<td id="month_(\d+)"[^>]*onclick="javascript:selectDay\(\d+\);".*?<img[^>]*?alt="(全て空き|一部空き|予約あり)"', re.S)

# **使用正则表达式提取下月可预约的日期**
matches = list(pattern.finditer(html_next_month))  # 先把匹配项存入列表

available_dates = []
partially_available_dates = []

if not matches:  # 如果 `matches` 为空
    logging.info(f"⚠️ {month_text} 空位未开放查询")
else:
    for match in matches:
        date_number = match.group(1)
        status = match.group(2)

        if status == "全て空き":
            available_dates.append(date_number)
        elif status == "一部空き":
            partially_available_dates.append(date_number)

if available_dates != []:
    logging.info(f"{month_text}可预约的日期（完全空闲）：{available_dates}")
    logging.info(f"{month_text}可预约的日期（部分空闲）：{partially_available_dates}")
    
    """
    # 🎌 **过滤掉非休日 & 非祝日的日期**
    def is_holiday_or_weekend(date_str):
        #检查日期是否为日本的周六、周日或祝日
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.weekday() in [5, 6] or jpholiday.is_holiday(date_obj)
    
    available_dates = [date for date in available_dates if is_holiday_or_weekend(date)]
    partially_available_dates = [date for date in partially_available_dates if is_holiday_or_weekend(date)]
    
    logging.info(f"{month_text}可预约的日期（完全空闲，仅休日&祝日）：{available_dates}")
    logging.info(f"{month_text}可预约的日期（部分空闲，仅休日&祝日）：{partially_available_dates}")
    """
    
    
    
    # 1️⃣4️⃣ **点击可预约的日期**
    for date in available_dates + partially_available_dates:
        logging.info(f"尝试点击日期：{date[:4]}年{date[4:6]}月{date[6:]}日")

        attempt = 0
        max_attempts = 3  # 允许最多重试 3 次

        while attempt < max_attempts:
            try:
                attempt += 1
                logging.info(f"🔄 尝试第 {attempt} 次点击 {date[:4]}年{date[4:6]}月{date[6:]}日")

                # 重新获取元素，确保元素有效
                date_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, f"month_{date}"))
                )

                date_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, f"month_{date}"))
                )
                date_element.click()
                logging.info(f"✅ 成功点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
                time.sleep(2)  # **短暂等待 JS 渲染**
                
                # ✅ **等待 `week-info` 确保时间段已加载**
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "week-info"))
                )
                logging.info(f"✅ {date[:4]}年{date[4:6]}月{date[6:]}日 的时间段已加载")

                # **获取最新 HTML**
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
                            "10": "9:00-11:30", "20": "11:30-13:30",
                            "30": "13:30-15:30", "40": "15:30-17:30",
                            "50": "17:30-19:30", "60": "19:30-22:00"
                        }.get(slot_suffix, "未知时间段")

                        availability_info[(slot_date, slot_time)] = available_count

                break  # 成功后退出循环

            except StaleElementReferenceException:
                logging.warning(f"⚠️ 目标元素失效，第 {attempt} 次重试 {date[:4]}年{date[4:6]}月{date[6:]}日...")
                time.sleep(1)  # 短暂等待，避免频繁请求

            except TimeoutException:
                logging.error(f"❌ 无法点击 {date[:4]}年{date[4:6]}月{date[6:]}日")
                driver.quit()
                exit(0)  # 终止程序




# **最终汇总**
logging.info("所有可预约时间段:")
for (date, time_slot), count in availability_info.items():
    logging.info(f"{date} | {time_slot}")

driver.quit()










import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 📩 **邮件发送函数**
def send_email(subject, body):
    sender_email = os.getenv("sender_email2") # 你的 Gmail 地址
    receiver_email = os.getenv("receiver_email").split(",") # 收件人邮箱
    password = os.getenv("password2")# Gmail 应用专用密码

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

# 📂 **读取上次的预约信息**
last_file = "last_availability_okubo.txt"
if os.path.exists(last_file):
    with open(last_file, "r", encoding="utf-8") as f:
        last_availability_okubo = f.read()
else:
    last_availability_okubo = ""

# 📌 **按照 日期 和 时间 进行排序**
time_order = {
    "9:00-11:30": 1, "11:30-13:30": 2,
    "13:30-15:30": 3, "15:30-17:30": 4, "17:30-19:30": 5, "19:30-22:00": 6
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
    f"{date[:4]}-{date[4:6]}-{date[6:]} ({weekday_japanese[datetime.strptime(date, '%Y%m%d').weekday()]}) | {time_slot} "
    for (date, time_slot), count in sorted_availability
])

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


