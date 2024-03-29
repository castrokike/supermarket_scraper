# Import libraries
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Other imports
import re as re
import pandas as pd

from dotenv import load_dotenv
load_dotenv()


months = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}

def convert_date_string(date_string):

    """
    Convert a date string from the format "Día de mes de Año" (e.g., "25 de enero de 2022") 
    to a pandas datetime object.
    
    Args:
        date_string: str, A date string in the format "Día de mes de Año"
    
    Returns:
        A pandas datetime object representing the input date.
    """

    # Extract the day and month name from the string using string manipulation functions
    day = int(date_string.split()[1])
    month_name = date_string.split()[3]
    
    # Map the month name to month number using the months dictionary
    month = months[month_name]
    
    # Determine the year based on the month
    year = 2022 if (month <= 12 and month >=10) else 2023
    
    # Combine the year, month, and day into a datetime object
    return pd.to_datetime(f"{year}-{month}-{day}")

def get_purchase_history(zip, mercadona_user, mercadona_password, headless=True):

    """
    Retrieves the purchase history of a user from Mercadona's online store.

    Args:
        zip (str): Postal code of the user's address.
        mercadona_user (str): Email address of the user's Mercadona account.
        mercadona_password (str): Password of the user's Mercadona account.
        headless (bool): Whether to run the web driver in headless mode (default True).

    Returns:
        pandas.DataFrame: Dataframe containing the purchase history of the user.
    """

    # Create a ChromeOptions object
    options = Options()

    # Add the headless argument if passed
    if headless:
        options.add_argument('--headless')

    # Specify the path to your web driver
    driver = webdriver.Chrome(options=options)

    # Navigate to the login page
    driver.get('https://www.mercadona.es/')

    # Enter the postal code and submit it
    postal_code = driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Código postal"]').send_keys(zip)
    submit_button = driver.find_element(By.CSS_SELECTOR, 'input.postal-code-form__button').click()

    # Accept cookies
    accept_button = driver.find_element(By.XPATH, "//button[contains(text(),'Aceptar todas')]").click()

    # Wait for the page to load
    driver.implicitly_wait(10)

    # Click the user dropdown and click the "Identifícate" button
    drop_down = driver.find_element(By.CSS_SELECTOR, 'button[class="drop-down__trigger"]')
    drop_down.click()
    identificate = driver.find_element(By.CSS_SELECTOR,'a[href="/?authenticate-user="]').click()
   
    # Enter the email address
    email = driver.find_element(By.CSS_SELECTOR, 'input[name="email"]')
    email.send_keys(mercadona_user)

    # Click the "Siguiente" button
    next_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    next_button.click()

    # Enter the password
    password = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    password.send_keys(mercadona_password)

    # Click the "Entrar" button
    entrar_button = driver.find_element(By.CSS_SELECTOR, 'button[data-test="do-login"]')
    entrar_button.click()

    # Wait up to 10 seconds for the element to become visible
    personal_section = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CLASS_NAME, 'account__user-name')
        )
    )
    personal_section.click()
  
    # Open "Mis pedidos"
    pedidos = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'a[href="/user-area/orders"]')
        )
    )
    pedidos.click()

    # Get all order numbers:
    order_nums = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, 'span[class="order-cell__id footnote1-r"]')
        )
    )
    
    # Create an empty list to store the order numbers
    list_of_orders = []

    # Extract the order numbers from order_nums and append them to list_of_orders
    for pedido in order_nums:
        list_of_orders.append(pedido.text.split(' ')[1])

    # Create an empty dataframe to store the details of every product in every order
    pedidos_to_return = pd.DataFrame({})

    # Loop over the order numbers and extract the order details
    for order_text in list_of_orders:

        # Visit the order details page
        driver.get(f"https://tienda.mercadona.es/user-area/orders/{order_text}?products")

        # Initialize an empty dictionary that will later be turned into a DataFrame. This dictionary will contain the information every product for an order
        order_details = {}
        
        # Get all products in the order
        products = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, 'p[class="order-product-cell__name subhead1-r"]')
            )
        )

        # Extract the text from each product element and store them in a list
        products_list = []
        for product in products:
            products_list.append(product.text)
        
        # Add the products list to the order details dictionary
        order_details["product"] = products_list

        # Get all units in the order
        units = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, 'span[class="order-product-cell__prepared-units subhead1-r"]')
            )
        )

        # Extract the number of units from each unit element and store them in a list
        units_list = []
        for unit in units:
            units_list.append(int(unit.text.split(' ')[0]))
        
        # Add the units list to the order details dictionary
        order_details["units"] = units_list
        
        # Get all prices in the order
        prices = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, 'p[class="order-product-cell__price subhead1-r"]')
            )
        )

        # Extract the price from each price element and store them in a list
        prices_list = []
        for price in prices:
            prices_list.append(float(price.text.split(' ')[0].replace(',','.')))
        
        # Add the prices list to the order details dictionary
        order_details["price"] = prices_list

        # Convert the order details dictionary to a dataframe and add the order number to each row
        order_details_df = pd.DataFrame(order_details)
        order_details_df = order_details_df.assign(order_number=order_text)

        # Get the delivery date and add it to the dataframe
        delivery = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, 'span[class="body1-b"]')
            )
        )
        order_details_df = order_details_df.assign(fecha=delivery[0].text)

        # Convert the text date to a Pandas DateTime element using our previous function.
        order_details_df["fecha"] = order_details_df["fecha"].apply(convert_date_string)

        # Add the order details dataframe to the overall dataframe
        pedidos_to_return = pd.concat([pedidos_to_return,order_details_df],ignore_index=True)

    print("Success!")
    return pedidos_to_return

def get_categories_from_scraping(csv):

    """
    Extracts product categories from a CSV file and returns a dataframe 
    with the product name, category, subcategory and code. 

    Args:
        csv (str): the path to the CSV file containing the scraped data

    Returns:
        pandas.DataFrame: a cleaned dataframe with the product categories
    """

    # Read the CSV file into a dataframe
    cat_codes = pd.read_csv(csv, sep='~')

    # Convert the 'product_code' column to integer data type
    cat_codes['product_code'] = cat_codes['product_code'].astype(int)

    # Remove the ' >' from the end of the 'product_category' column
    cat_codes["product_category"] = cat_codes["product_category"].str.replace(" >","")

    # Remove '|' from the 'product_price_per_unit' column
    cat_codes["product_price_per_unit"] = cat_codes["product_price_per_unit"].str.replace("|","")

    # Remove '/' and '.' from the 'product_unit' column
    cat_codes["product_unit"] = cat_codes["product_unit"].str.replace("/","").str.replace(".","")

    # Return a cleaned dataframe with the 'product', 'product_category', 'product_subcategory', and 'product_code' columns and remove any duplicates
    return cat_codes[['product','product_category', 'product_subcategory', 'product_code']].drop_duplicates()



# The following dictionaries are used to replace product codes based on my behaviour. If this were to be scaled up these replacement would need to be done in another way.
product_dict = {"Ensalada mezcla brotes tiernos maxi" : 69810,
"Bebida de almendras zero Hacendado" : 23926,
"Papel higiénico húmedo WC Bosque Verde" : 47291,
"Detergente ropa All in 1 Ariel Pods en cápsulas" : 16806,
"Servilleta papel Bosque Verde" : 49544,
"Acondicionador Repara & Protege Pantene" : 35615,
"Detergente ropa All in 1 Ariel en cápsulas" : 16806,
"Champú Anticaída Deliplus" : 44356,
"Servilleta papel Cocktail Bosque Verde" : 49544,
"Filetes pechuga de pollo corte fino" : 3400,
"Ambientador automático Caramel Bosque Verde" : 72405,
"Champú Anticaída Men Deliplus" : 44355,
"Activador quitamanchas ropa de color Oxi Active Bosque Verde en polvo" : 40317,
"Disuelve manchas Bosque Verde" : 40178,
"Activador Blanqueante ropa blanca Bosque Verde en polvo" : 40315,
"Galletas cacahuete y chocolate Hacendado" : 0,
"Papel vegetal Bosque Verde" : 23608,
"Galletas crujientes chocolate y avena Hacendado" : 0,
"Galletas mini Oreo" : 14030,
"Salteado de setas laminadas" : 69674,
"Barritas Sustitutivo de comida Belladieta sabor avena y chocolate con leche" : 86259,
"Manzana Royal Gala" : 3175,
"Vela perfumada Té Chai Bosque Verde" : 15805}

code_replacement = {
        4717 : 4718,        # "Aceite de oliva virgen extra Hacendado" : 4718
        4740 : 4718,
        29007 : 29006,      # "Bicarbonato sódico Hacendado" : 29006
        31504 : 31003,      # "Huevos grandes L" : 31003
        31540 : 31003,
        10730 : 10731,      # "Leche desnatada sin lactosa Hacendado" : 10731
        20722 : 20727,      # "Mantequilla con sal Hacendado" : 20727
        59247 : 59252,      # "Pechuga de pavo bajo en sal Hacendado finas lonchas" : 59252
        3724 : 3682,        # "Pechugas enteras de pollo" : 3682
        2868 : 3454,        # "Preparado de carne picada vacuno" : 3454
        2869 : 3453,        # "Preparado de carne picada vacuno y cerdo" : 3453
        27559 : 26997,
        28180 : 26997,
        27462 : 26997,       # "Refresco Coca-Cola Zero Zero" : 26997
        27414 : 27426,
        27449 : 27426,
        27445 : 27426,
        13816 : 27426,
        28115 : 27426,
        29361 : 27426,       # "Refresco Coca-Cola Zero azúcar" : 27426
        53444 : 53445,       # "Salmón ahumado Hacendado" : 53445
        6245 : 6331,         # "Spaghetti Hacendado" : 6331
        79603 : 79427,
        79428 : 79427,       # "Toallitas bebé frescas & perfumadas Deliplus" : 79427
        39033 : 39010        # "Zumo pura naranja Hacendado" : 39010
}

def assign_product_codes(cat_codes, orders):

    """
    This function assigns product codes to a dataframe of orders based on a separate dataframe containing category codes.
    
    Parameters:
        cat_codes (pandas.DataFrame): A dataframe containing category codes for products.
        orders (pandas.DataFrame): A dataframe containing orders for products.
    
    Returns:
        pandas.DataFrame: A dataframe of orders with product codes assigned.
    """

    # Merge orders and category codes dataframes
    order_history = pd.merge(orders, cat_codes[["product", "product_code"]],left_on="product", right_on="product", how="left")
    
    # Fill missing product codes with product_dict
    order_history["product_code"] = order_history["product_code"].fillna(order_history["product"].map(product_dict))
    
    # Convert product codes to integers
    order_history['product_code'] = order_history['product_code'].astype(int)

    # The following lines are an alternate way to deal with transforming the product code to int.
    #order_history['product_code'] = pd.to_numeric(order_history['product_code'], errors='coerce')
    #order_history['product_code'] = order_history['product_code'].fillna(order_history['product_code'].astype(str))
    
    # Calculate price per unit for each product
    order_history['price_per_unit'] = order_history['price'] / order_history['units']

    # Replace product codes with code_replacement
    order_history["product_code"] = order_history["product_code"].replace(code_replacement)

    # Drop duplicate rows
    order_history = order_history.drop_duplicates()

    # Return dataframe with product codes assigned
    return order_history