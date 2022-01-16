import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException


class BaseChrome(object):
    """将selenium的Chrome的常用方法进行封装"""

    click_type = ['element_click', 'js_click']
    find_by_value = [getattr(By, key) for key in By.__dict__.keys() if not key.startswith("__")]

    def __init__(self, executable_path="chromedriver", port=0, service_args=None,
                 desired_capabilities=None, service_log_path=None,
                 chrome_options=None, keep_alive=True):

        """ --- 创建chrome驱动程序的新实例 ---
        :param executable_path: 可执行文件的路径,如果使用默认值,则假定可执行文件位于$PATH中
        :param port: 希望服务运行的端口,如果保留为0,将使用一个空闲随机端口
        :param service_args: 要传递给驱动程序服务的参数列表
        :param desired_capabilities: 具有非特定于浏览器的字典对象,仅限功能,如“代理”或“loggingPref”
        :param service_log_path: 记录驱动程序信息的位置
        :param chrome_options: 不推荐的选项参数
        :param keep_alive: 是否将ChromeRemoteConnection配置为使用HTTP keep alive
        """
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(executable_path=executable_path, port=port,
                                       options=self.chrome_options(),
                                       service_args=service_args,
                                       desired_capabilities=desired_capabilities,
                                       service_log_path=service_log_path,
                                       chrome_options=chrome_options,
                                       keep_alive=keep_alive)

    def chrome_options(self):
        r"""
        ChromeOptions:
            # 禁用弹出保存弹窗
            self.options.add_experimental_option("profile.default_content_settings.popups", 0)
            # 修改默认下载路径
            self.options.add_experimental_option("download.default_directory", "C:\Users")
            # 允许多文件下载
            self.options.add_experimental_option("profile.default_content_setting_values.automatic_downloads", 1)
        """
        return self.options

    def quit_browser(self):
        self.driver.quit()

    def find_element(self, by="xpath", value=None, timeout=5):
        """查找页面中Element元素
        :param by: 获取页面元素的类型: self.find_by_value
        :param value: 获取元素所需的值
        :param timeout: 超时时间
        :return: WebElement
        """
        if by not in self.__class__.find_by_value:
            raise ValueError(f"Parameter is out of range: {by}")
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                return self.driver.find_element(by=by, value=value)
            except NoSuchElementException:
                time.sleep(0.2)
        return None

    def find_elements(self, by="xpath", value=None, timeout=5):
        """查找页面中Element元素
        :param by: 获取页面元素的类型: self.find_by_value
        :param value: 获取元素所需的值
        :param timeout: 超时时间
        :return: WebElement List
        """
        if by not in self.__class__.find_by_value:
            raise ValueError(f"Parameter is out of range: {by}")
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                return self.driver.find_elements(by=by, value=value)
            except NoSuchElementException:
                time.sleep(0.2)
        return None

    def remove_attribute(self, element: WebElement, name: str):
        """删除Element中某个属性
        :param element: WebElement Object
        :param name: Attribute Name
        :return: None
        """
        self.driver.execute_script("arguments[0].removeAttribute(arguments[1])", element, name)

    def set_attribute(self, element: WebElement, name: str, value=None):
        """在Element中修改属性值, 如果属性不存在则增加
        :param element: WebElement Object
        :param name: Attribute Name
        :param value: Attribute Value
        :return: Attribute Value
        """
        # 如果value为空则将value设置为当前"时分秒"
        if not value:
            value = time.strftime("%H%M%S")
        self.driver.execute_script(f"arguments[0].setAttribute('{name}', arguments[1]);", element, value)
        return value

    def element_click(self, element: WebElement, click_type="element_click"):
        """页面中Element元素点击
        注意: JS点击后WebElement对象会被释放,如再用到需再次捕获
        :param element: WebElement Object
        :param click_type: -> ['element_click', 'js_click']
        :return: None
        """
        if click_type not in self.__class__.click_type:
            raise ValueError(f"Parameter is out of range: {click_type}")
        if click_type == "element_click":
            return element.click()
        """setInterval(function() {document.getElementById("ID").click();}, 500)"""
        self.driver.execute_script("arguments[0].click();", element)

    def get_text(self, element: WebElement):
        """利用JavaScript获取WebElement中的文本
        :param element: WebElement Object
        :return: Text
        """
        return self.driver.execute_script('return arguments[0].innerText', element)

    def scroll_to(self, x=None, y=None):
        """利用JavaScript滚动当前页面, 坐标如为空则滚动到最底部
        :param x: 页面横坐标
        :param y: 页面纵坐标
        :return: None
        """
        if x is None and y in None:
            return self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.execute_script(f"window.scrollTo({x},{y})")

    def catch_by_title(self, title: str):
        """切换到指定窗口标题的窗口,如果没找到则返回默认窗口
        :param title: 窗口标题名: 完整标题或全部标题名中的一部分
        :return: Bool
        """
        handles = self.driver.window_handles
        if len(handles) == 1:
            if title in self.driver.title:
                return True
            return False
        original_window = self.driver.current_window_handle
        handles.remove(original_window)
        for handle in handles:
            self.driver.switch_to.window(handle)
            if title in self.driver.title:
                return True
        self.driver.switch_to.window(original_window)
        return False

    def catch(self, url: str):
        """切换到指定URL的窗口,如果没找到则返回默认窗口
        :param url: url链接: 完整url或url中的一部分
        :return: Bool
        """
        handles = self.driver.window_handles
        if len(handles) == 1:
            if url in self.driver.current_url:
                return True
            return False
        original_window = self.driver.current_window_handle
        handles.remove(original_window)
        for handle in handles:
            self.driver.switch_to.window(handle)
            if url in self.driver.current_url:
                return True
        self.driver.switch_to.window(original_window)
        return False

    def wait_title_change(self, title: str, timeout=5):
        """等待当前标签页的标题发生改变
        :param title: 标签页标题(完整标题或实际标题中的一部分)
        :param timeout: 等待超时时间
        :return: Bool
        """
        # 构建一个超时实例
        wait = WebDriverWait(self.driver, timeout)
        try:
            # 使用expected_conditions中的功能类来判断某一项任务是否发生改变
            return wait.until(expected_conditions.title_contains(title))
        except TimeoutException:
            return False

    def switch_to_frame(self, value, by="WebElement"):
        """页面中切换frame
        by可分为: frame元素对象, frame元素id属性值, frame索引数字(第几个frame)

        use:
        -   frame = driver.find_element(by=By.XPATH, value="//iframe[@class="mainframe"]")
            driver.switch_to_frame(value=frame, by="id")

        -   driver.switch_to_frame(value="mainframe", by="id")

        -   driver.switch_to_frame(value=0, by="index")

        :param value: 指定by参数的frame值
        :param by: -> ["WebElement", "id", "index"]
        :return: None
        """
        if by in ['element', 'id']:
            self.driver.switch_to.frame(value)
        elif by == 'index':
            iframe = self.driver.find_elements_by_tag_name('iframe')[value]
            self.driver.switch_to.frame(iframe)
        else:
            raise ValueError(f"Parameter is out of range: {by}")

    def frame_to_available_and_switch(self, value, timeout=5):
        """等待frame框架可用并切换到它
        :param value: frame值: id属性值 or WebElement
        :param timeout: 等待超时时间
        :return: 切换成功返回True,否则报错: exceptions.TimeoutException
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(expected_conditions.frame_to_be_available_and_switch_to_it(value))

    def new_window(self, url: str):
        """利用JavaScript创建新的标签页
        :param url: 目标URL
        :return: None
        """
        self.driver.execute_script(f'window.open("{url}")')

    def is_alert_loaded(self, timeout=5):
        """检测当前
        :param timeout: 等待超时时间
        :return: Bool
        """
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                return self.driver.switch_to.alert
            except NoAlertPresentException:
                time.sleep(0.2)
        return False
