from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from weasyprint import HTML
from time import sleep
import os

LINK = "https://trmangaoku.com/manga/blue-lock/bolum-215/"


"""
Türkçe: 
Mangalarımı bu site üzerinden okuyorum. Ancak, sizler kod üzerinde birkaç değişiklik yaparak, bu aracın diğer sitelerde de çalışmasını sağlayabilirsiniz. Bu projeyi hayata geçirmemin en temel nedeni, internetsiz kaldığım zamanlardaki can sıkıntımı bir nebze olsun azaltacak kaynaklar toplayabilmemdir. Bu, benim çocukluğumdan kalma bir alışkanlıktır. Bu araç ile siz de mangalarınızı, benim gibi depolayabilir ve daha sonra tekrar okumak için saklayabilirsiniz.

English:
I read my manga on this site, but you can make a few changes to the code to make this tool work on other sites as well. The main reason why I started this project is to collect resources that will help me alleviate some of my boredom when I am without internet. This is a habit I have from my childhood. With this tool, you too can store your manga like I did and save them to read again later.

"""


options = Options()
options.add_experimental_option("detach", True)  
options.add_experimental_option("excludeSwitches", ["enable-automation"])  
options.add_experimental_option('useAutomationExtension', False)  
options.add_argument("--disable-blink-features=AutomationControlled")  
options.add_argument("--disable-popup-blocking")  
options.add_argument("--disable-save-password-bubble")  
options.add_argument("--disable-notifications")  
options.add_argument("--incognito")  
options.add_argument("--start-maximized") 
options.add_argument("--headless")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

driver.get(LINK)

try:
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".page-break.no-gaps"))
    )

    actions = ActionChains(driver)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    
    elements = driver.find_elements(By.CSS_SELECTOR, ".page-break.no-gaps")

    images = []
    
    
    for element in elements:
        image = element.find_element(By.TAG_NAME, "img")  
        image_url = image.get_attribute("src")  
        images.append(image_url)
    

    print("Please don't use . in manga name")
    mangaName = input("Enter manga name: ") + ".html"
    pdfName = mangaName.replace(".html", ".pdf")

    
    with open(mangaName, "w", encoding="utf-8") as file:
        file.write("<!DOCTYPE html>\n")
        file.write("<html lang='en'>\n")
        file.write("<head>\n")
        file.write("<meta charset='UTF-8'>\n")
        file.write("<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n")
        file.write("<title>Manga Images</title>\n")
        file.write("</head>\n")
        file.write("<body>\n")
        
        for image_url in images:
            file.write(f"<img src='{image_url}' alt='Manga Image' style='width:100%;'><br>\n")
        
        file.write("</body>\n")
        file.write("</html>\n")

    
    
    sleep(15) # wait for images to load becaause your internet connection can be slow , this is an garanty way to make sure images are loaded

    HTML(mangaName).write_pdf(pdfName)
    os.remove(mangaName)
    
    
except Exception as e:
    print(f"Hata oluştu: {e}")
finally:
    driver.quit()
