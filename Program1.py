# Delete an element or list of element in python
x = 10
print(x)  # Output: 10
del x
print(x)  # This will raise a NameError, since 'x' is deleted


a = [1, 2, 3]
b = a  # b references the same list as a
del a  # Now 'a' is deleted, but the list is still referenced by 'b'
print(b)  # Output: [1, 2, 3]
import scrapy
import re
import json
from scrapy.crawler import CrawlerProcess
from flipkart_scraper.items import FlipkartScraperItem
from flipkart_scraper.pipelines import FlipkartScraperPipeline  # ✅ Import pipeline

class FlipkartSpider(scrapy.Spider):
    name = "flipkart"
    start_urls = ["https://www.flipkart.com"]

    def __init__(self, *args, **kwargs):
        """Initialize the pipeline manually for direct item processing."""
        super().__init__(*args, **kwargs)
        self.pipeline = FlipkartScraperPipeline()  # ✅ Initialize pipeline
        self.pipeline.open_spider(self)  # ✅ Open database connection

    def parse(self, response):
        """Extract category and subcategory data from Flipkart."""
        html_text = response.text

        # ✅ Fix: Extract only first JSON block using regex
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;\s*</script>', html_text, re.DOTALL)
        if not match:
            self.logger.error("❌ Could not find JSON data in the response")
            return

        json_str = match.group(1).strip()

        try:
            # ✅ Fix: Ensure safe JSON parsing
            data = json.loads(json_str)

            slots = data.get('multiWidgetState', {}).get('widgetsData', {}).get('slots', [])
            if not isinstance(slots, list):
                self.logger.error("❌ Slots data is not in expected format")
                return

            for slot in slots:
                if not isinstance(slot, dict):
                    continue

                widget_data = slot.get('slotData', {}).get('widget', {}).get('data', {})
                renderable_components = widget_data.get('renderableComponents', [])

                # level 1
                for component in renderable_components:
                    category_name = component.get('value', {}).get('text', '')
                    category_url = component.get('action', {}).get('url', '')

                    subcategories = component.get('value', {}).get('items', [])

                    # ✅ Create Scrapy item
                    item = FlipkartScraperItem(
                        category_name=category_name,
                        category_url=category_url,
                        subcategory_name=None,
                        subcategory_url=None,
                        subsubcategory_name=None,
                        subsubcategory_url=None,
                        category_path=category_name,
                        status='pending'
                    )

                    if subcategories != []:  # ✅ If there are no subcategories, process manually
                        self.pipeline.process_item(item, self)  # ✅ Manually process item

                    #level 2
                    for sub in subcategories:
                        subcategory_name = sub.get('value', {}).get('text', '')
                        subcategory_url = sub.get('action', {}).get('url', '')

                        subsubcategories = sub.get('value', {}).get('items', [])

                        if subcategory_name.lower() == "all":
                            continue

                        item = FlipkartScraperItem(
                            category_name=category_name,
                            category_url=category_url,
                            subcategory_name=subcategory_name,
                            subcategory_url=subcategory_url,
                            subsubcategory_name=None,
                            subsubcategory_url=None,
                            category_path=f'{category_name} > {subcategory_name}',
                            status='pending'
                        )
                        if subsubcategories != []:  # ✅ If there are no subcategories, process manually
                            self.pipeline.process_item(item, self)
                        # self.pipeline.process_item(item, self)

                        #level 3
                        for subsub in subsubcategories:
                            subsubcategory_name = subsub.get('value', {}).get('text', '')
                            subsubcategory_url = subsub.get('action', {}).get('url', '')

                            if subsubcategory_name.lower() == "all":
                                continue

                            item = FlipkartScraperItem(
                                category_name=category_name,
                                category_url=category_url,
                                subcategory_name=subcategory_name,
                                subcategory_url=subcategory_url,
                                subsubcategory_name=subsubcategory_name,
                                subsubcategory_url=subsubcategory_url,
                                category_path=f'{category_name} > {subcategory_name} > {subsubcategory_name}',
                                status='pending'
                            )
                            self.logger.info(f"📌 Extracted item: {item}")
                            self.pipeline.process_item(item, self)


        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decoding failed: {e}")

    def closed(self, reason):
        """Ensure the pipeline closes the database connection when the spider stops."""
        self.pipeline.close_spider(self)  # ✅ Close database connection

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
    })
    process.crawl(FlipkartSpider)
    process.start()



import logging
import pymysql

class FlipkartScraperPipeline:
    def open_spider(self, spider):
        """Connect to MySQL when the spider starts"""
        try:
            self.conn = pymysql.connect(
                host='localhost',
                user='root',
                password='actowiz',
                database='flipkart',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            logging.info("✅ Connected to MySQL successfully!")

            # Ensure tables exist
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS flipkart_data1
                 (
                    sr_no INT AUTO_INCREMENT PRIMARY KEY,
                    category_name VARCHAR(255),
                    category_url TEXT,
                    subcategory_name VARCHAR(255),
                    subcategory_url TEXT,
                    subsubcategory_name VARCHAR(255),
                    subsubcategory_url TEXT,
                    category_path TEXT,
                    total_count INT DEFAULT NULL,
                    inserted_count INT DEFAULT NULL,
                    status VARCHAR(50) DEFAULT 'pending'
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS flipkart_pdp (
                    sr_no INT AUTO_INCREMENT PRIMARY KEY,
                    subsubcategory_url TEXT,
                    product_url TEXT,
                    category_path TEXT,
                    category_position INT,
                    page_number INT
                )
            """)
            self.conn.commit()
            logging.info("✅ Tables verified/created successfully!")

        except pymysql.MySQLError as e:
            logging.error(f"❌ MySQL connection error: {e}")
            raise

    def process_item(self, item, spider):
        """Insert categories and products into the database"""
        try:
            logging.info(f"📌 Processing item: {item}")
            if spider.name == 'flipkart':  # ✅ Fix: Handle category data
                self.cursor.execute("""
                    INSERT INTO flipkart_data1 
                    (category_name, category_url, subcategory_name, subcategory_url, subsubcategory_name, subsubcategory_url, category_path, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item['category_name'],
                    item['category_url'],
                    item['subcategory_name'],
                    item['subcategory_url'],
                    item['subsubcategory_name'],
                    item['subsubcategory_url'],
                    item['category_path'],
                    item['status']
                ))
                self.conn.commit()
                logging.info(f"✅ Inserted category: {item['category_name']}")

            elif spider.name == 'flipkart_product':  # ✅ Fix: Handle product data
                for product in item['dlist']:
                    self.cursor.execute("""
                        INSERT INTO flipkart_pdp 
                        (subsubcategory_url, product_url, category_path, category_position, page_number)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        product['subsubcategory_url'],
                        product['product_url'],
                        product['category_path'],
                        product['category_position'],
                        product['page_number']
                    ))
                self.conn.commit()
                logging.info(f"✅ Inserted {len(item['dlist'])} products for {item['sub_url']}")

        except pymysql.MySQLError as e:
            logging.error(f"❌ MySQL error inserting item: {e}")
            self.conn.rollback()

        return item

    def close_spider(self, spider):
        """Close MySQL connection when the spider stops"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logging.info("✅ MySQL connection closed successfully.")







import pymysql
import scrapy
import re
from scrapy.cmdline import execute
# from flipkart_scraper.flipkart_scraper.items import justanitem
from flipkart_scraper.items import justanitem

class FlipkartProductSpider(scrapy.Spider):
    name = "flipkart_product"
    allowed_domains = ["flipkart.com"]
    start_urls = ["https://www.flipkart.com"]

    insert_counts = {}

    def __init__(self, *args, **kwargs):
        """Initialize MySQL connection when the spider starts."""
        super().__init__(*args, **kwargs)
        self.conn = pymysql.connect(
            host='localhost',
            user='root',
            password='actowiz',
            database='flipkart',
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()

        # ✅ Ensure `flipkart_data` table exists before querying
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS flipkart_data1 (
                sr_no INT AUTO_INCREMENT PRIMARY KEY,
                subsubcategory_url VARCHAR(1000) UNIQUE,
                category_path TEXT,
                total_count INT DEFAULT NULL,
                inserted_count INT DEFAULT NULL,
                status VARCHAR(50) DEFAULT 'pending'
            )
        """)
        self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS flipkart_pdp (
                        sr_no INT AUTO_INCREMENT PRIMARY KEY,
                        subsubcategory_url TEXT,
                        product_url TEXT,
                        category_path TEXT,
                        category_position INT,
                        page_number INT
                    )
                """)
        self.conn.commit()

    def parse(self, response):
        """Fetch category data from MySQL and start scraping."""
        try:
            column_data = self.fetch_pending_subcategories()
        except Exception as e:
            self.logger.error(f"❌ Error fetching data from SQL: {e}")
            column_data = []

        for data in column_data:
            subsubcategory_url = data.get('subsubcategory_url', '')
            category_path = data.get('category_path', '')

            if subsubcategory_url:
                self.insert_counts[subsubcategory_url] = 0  # ✅ Initialize inserted count tracking
                yield scrapy.Request(
                    url=subsubcategory_url,
                    callback=self.parse_product_page,
                    meta={'subsubcategory_url': subsubcategory_url, 'category_path': category_path, 'page': 1}
                )

    def parse_product_page(self, response):
        """Extract product data and update database."""
        subsubcategory_url = response.meta.get('subsubcategory_url', '')
        category_path = response.meta.get('category_path', '')
        current_page = response.meta.get('page', 1)

        # ✅ Improved `total_count` extraction
        total_count_text = response.xpath('//span[contains(text(), "of")]/text()').get()
        self.logger.info(f"Extracted total count text: {total_count_text}")

        total_count = None
        if total_count_text:
            match = re.search(r'of\s([\d,]+)', total_count_text)
            if match:
                total_count = match.group(1).replace(',', '')

        if total_count:
            self.update_total_count(subsubcategory_url, total_count)

        # Extract product URLs
        product_containers = response.css('a[href*="/p/"]::attr(href)').getall()
        data_list = []

        for index, product_url in enumerate(product_containers, start=1):
            absolute_url = response.urljoin(product_url.strip())
            data_list.append({
                'product_url': absolute_url,
                'subsubcategory_url': subsubcategory_url,
                'category_path': category_path,
                'category_position': index + ((current_page - 1) * len(product_containers)),
                'page_number': current_page
            })

        dfdf = justanitem()  # ✅ Ensure correct case
        dfdf['sub_url'] = subsubcategory_url
        dfdf['dlist'] = data_list
        yield dfdf

        # ✅ Prevent KeyError in `insert_counts`
        if subsubcategory_url not in self.insert_counts:
            self.insert_counts[subsubcategory_url] = 0

        self.insert_counts[subsubcategory_url] += len(data_list)
        total_inserted_count = self.insert_counts[subsubcategory_url]
        self.update_insert_count(subsubcategory_url, total_inserted_count)

        # ✅ Improved Pagination (No hard stop at 50 pages)
        next_page_url = response.css('a._1LKTO3::attr(href)').get()
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse_product_page, meta=response.meta)
        else:
            self.update_status_to_completed(subsubcategory_url)

    def fetch_pending_subcategories(self):
        """Fetch subsubcategory URLs with 'pending' status from the database."""
        try:
            self.cursor.execute("""
                SELECT subsubcategory_url, category_path 
                FROM flipkart_data1 
                WHERE status = 'pending'
            """)
            rows = self.cursor.fetchall()
            return [{'subsubcategory_url': row[0], 'category_path': row[1]} for row in rows]
        except pymysql.MySQLError as e:
            self.logger.error(f"❌ MySQL error: {e}")
            return []

    def update_total_count(self, subsubcategory_url, total_count):
        """Update the total count in the database."""
        try:
            self.cursor.execute("""
                UPDATE flipkart_data1
                SET total_count = %s
                WHERE subsubcategory_url = %s
            """, (total_count, subsubcategory_url))
            self.conn.commit()
        except pymysql.MySQLError as e:
            self.logger.error(f"❌ MySQL error updating total count: {e}")

    def update_insert_count(self, subsubcategory_url, total_inserted_count):
        """Update the total inserted count in the database."""
        try:
            self.cursor.execute("""
                UPDATE flipkart_data1
                SET inserted_count = %s
                WHERE subsubcategory_url = %s
            """, (total_inserted_count, subsubcategory_url))
            self.conn.commit()
        except pymysql.MySQLError as e:
            self.logger.error(f"❌ MySQL error updating inserted count: {e}")

    def update_status_to_completed(self, subsubcategory_url):
        """Mark subsubcategory URL as completed in the database."""
        try:
            self.cursor.execute("""
                UPDATE flipkart_data1 
                SET status = 'completed' 
                WHERE subsubcategory_url = %s
            """, (subsubcategory_url,))
            self.conn.commit()
            self.logger.info(f"✅ Updated status to 'completed' for {subsubcategory_url}")
        except pymysql.MySQLError as e:
            self.logger.error(f"❌ MySQL error updating status: {e}")

    def closed(self, reason):
        """Close MySQL connection when the spider stops."""
        self.conn.close()
        self.logger.info("✅ MySQL connection closed successfully.")


if __name__ == "__main__":
    execute('scrapy crawl flipkart_product'.split())
