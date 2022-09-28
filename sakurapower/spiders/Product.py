import json
import os

import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


def image_name_beautifier(image_name):
    return image_name.translate({ord(c): " " for c in "'\","})


def process_image_url(image_arr):
    return [img_url if img_url.startswith('http') else ('http:' + img_url) for img_url in image_arr]


class Category(scrapy.Spider):
    name = 'product'
    start_urls = set()

    if os.path.isfile("v1/product_url.json"):
        with open('v1/product_url.json') as json_file:
            data = json.load(json_file)
            for p in data:
                print(p)
                start_urls.add(p['product_url'])

    def start_requests(self):
        for u in self.start_urls:
            yield scrapy.Request(u, callback=self.parse, errback=self.err_back, dont_filter=True)

    def parse(self, response):
        page = response.xpath("//*[@id='product']/div/div/div[contains(@class,'product-essential')]/div[contains(@class,'product')]")
        product_info = page.xpath("//div[contains(@class,'product-info')]")

        name = product_info.xpath("./div[contains(@class,'product-info-header')]/h1/text()").get()

        price_path = product_info.xpath("//div[contains(@class,'product-price')]/div[contains(@class,'price')]/div[contains(@class,'price-box')]")

        short_description = ''
        short_description = short_description + product_info.xpath("./div[@class='product-warranty']/div[2]/b/text()").get() + " " + product_info.xpath("./div[@class='product-warranty']/div[2]/text()").get() + "\n"
        short_description_arr = product_info.xpath("./ul[@class='product-info-list']/p/text()|./ul[@class='product-info-list']/h3/text()").getall()
        short_description = short_description + "\n".join(short_description_arr)

        if not product_info.xpath("./ul[@class='product-info-list']/p"):
            short_description_arr = product_info.xpath("./ul[@class='product-info-list']/div/div/p/text()|./ul[@class='product-info-list']/div/div/h3/text()").getall()
            short_description = short_description + "\n".join(short_description_arr)
        else:
            short_description_arr = product_info.xpath("./ul[@class='product-info-list']/text()").getall()
            if len(short_description_arr) > 0:
                short_description = short_description + "\n".join(short_description_arr)

        description_path = page.xpath("//div[contains(@class,'product-tab')]/div[@id='product-tab-content']/div[@id='description']/div")
        description_tr = ''
        description_tr_arr = page.xpath("./table/tbody/tr|./div/div/div/div/table/tbody/tr")
        if description_tr_arr:
            for tr in description_tr_arr:
                if tr:
                    # tr_path = html.fromstring(tr)
                    td_arr = tr.xpath('./td/text()').getall()
                    description_tr = description_tr + " ".join(td_arr) + "\n"

        description_p = ''
        description_p_arr = description_path.xpath("./div/p/text()|./p/text()|./div/div/div/div/p/text()|./div/div/div/div/p/strong/span/text()|./div/div/div/div/p/strong/text()|./div/div/div/div/p/b/text()").getall()
        description_p = "\n".join(description_p_arr)

        description_div = ''
        if not description_p:
            description_div_arr = page.xpath("//div[contains(@class,'product-tab')]/div[@id='product-tab-content']/div[@id='description']/div/text()").getall()
            if len(description_div_arr) > 0:
                description_div = "\n".join(description_div_arr)

        description = description_tr + description_p + description_div

        product_img = page.xpath("//div[contains(@class,'product-image')]")
        image_arr = process_image_url(product_img.xpath("//img/@src").getall())
        images = set()
        for url in image_arr:
            img_file = image_name_beautifier(url.strip().split('/')[-1])
            images.add(img_file)

        category = response.xpath('//*[@id="page-header"]/div[2]/ul/li')
        categories = category.xpath('./a/text()').getall()
        categories.remove('Home')

        sale_price = ''
        regular_price = ''
        if price_path.xpath("./p[@class='special-price']/span[@class='price']/text()").get():
            sale_price = price_path.xpath("./p[@class='special-price']/span[@class='price']/text()").get()
            regular_price = price_path.xpath("./p[@class='old-price']/span[@class='price']/text()").get()
        else:
            regular_price = price_path.xpath("./span[@class='regular-price']/span[@class='price']/text()").get()

        product = {
            'SL NO': '',
            'Type': 'simple',
            'SKU': '',
            'Name': name.strip(),
            'Published': 1,
            'Is featured?': 0,
            'Visibility in catalog': 'visible',
            'Short Description': short_description,
            'Description': description,
            'In stock?': 1,
            'Sold individually?': 0,
            'Allow customer reviews?': 1,
            'Purchase note': 'Thanks for purchasing',
            'Sale price': sale_price,
            'Regular price': regular_price,
            'Categories': categories,
            'Tags': '',
            'Shipping class': 'Dhaka Only',
            'Images': ','.join(map(str, images)),
            'Position': 0,
            'Meta: _specifications_display_attributes': 'yes',
            'Meta: _per_product_admin_commission_type': 'percentage',
            'product-url': response.url,
            'image_url': image_arr,
        }

        yield product

    def err_back(self, failure):
        self.logger.error(repr(failure))

        f = open("failed_url.txt", "a")

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
            f.write('HttpError on ' + response.url)
            f.write("\n")

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
            f.write('DNSLookupError on ' + request.url)
            f.write("\n")

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
            f.write('TimeoutError on ' + request.url)
            f.write("\n")

        else:
            f.write('failure.value.response on ' + failure.value.response.url)
            f.write("\n")
            f.write('failure.request on ' + failure.request.response.url)
            f.write("\n")

        f.close()
