

from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

def search_product_images_with_selenium(query):
    # Set up Chrome options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration (useful for headless)
    options.add_argument("--no-sandbox")  # To handle sandboxing issues

    # Set the Chrome WebDriver with the service and options
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # List of search URLs for the three platforms
    search_urls = {
        "amazon": f"https://www.amazon.in/s?k={query.replace(' ', '+')}",
        "flipkart": f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    }
    
    product_images = {}

    try:
        for platform, search_url in search_urls.items():
            print(f"Searching on {platform.capitalize()}: {search_url}")
            
            # Navigate to the search URL
            driver.get(search_url)
            
            # Wait for the images to load (use WebDriverWait for more reliable waits)
            if platform == "amazon":
                # Amazon requires a bit more handling due to infinite scroll
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'search')))
                
                # Scroll down the page to load more products if needed
                for _ in range(3):  # Scroll a few times to ensure more products load
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for new content to load
            else:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
            
            # Find all image elements on the page
            image_elements = driver.find_elements(By.TAG_NAME, 'img')
            
            # Collect product image URLs for this platform
            images = []
            for idx, img in enumerate(image_elements):
                src = img.get_attribute('src')
                alt = img.get_attribute('alt')
                
                # Skip the specific Flipkart insurance image with the known src URL
                if platform == "flipkart" and (
                    src == "https://static-assets-web.flixcart.com/fk-p-linchpin-web/fk-cp-zion/img/fa_9e47c1.png" or
                    src == "https://static-assets-web.flixcart.com/fk-p-linchpin-web/fk-cp-zion/img/plus_aef861.png" or 
                    src == "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMyIgaGVpZ2h0PSIxMiI+PHBhdGggZmlsbD0iI0ZGRiIgZD0iTTYuNSA5LjQzOWwtMy42NzQgMi4yMy45NC00LjI2LTMuMjEtMi44ODMgNC4yNTQtLjQwNEw2LjUuMTEybDEuNjkgNC4wMSA0LjI1NC40MDQtMy4yMSAyLjg4Mi45NCA0LjI2eiIvPjwvc3ZnPg=="
                ):
                    continue
                
                if platform == "amazon" and src and idx >= 3:  # Skip the first 3 images on Amazon
                    images.append(src)
                elif platform != "amazon" and src:  # Include all images for other platforms
                    images.append(src)
            
            # Skip the last 6 images for Flipkart
            if platform == "flipkart":
                images = images[:-6]  # Remove the last 6 images from the list

            # Store the images for the current platform
            product_images[platform] = images

    except Exception as e:
        print(f"Error while fetching images: {e}")
    finally:
        # Close the driver after extraction
        driver.quit()
    
    return product_images



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the user input (product search query)
        user_query = request.form["query"]
        
        # Search for product images across all platforms
        product_images = search_product_images_with_selenium(user_query)
        
        # Ensure the results are a dictionary before passing it to the template
        results = product_images
        
        return render_template("index.html", results=results, query=user_query)
    
    return render_template("index.html", results=None)


if __name__ == "__main__":
     app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
