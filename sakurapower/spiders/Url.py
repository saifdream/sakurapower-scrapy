import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class Url(scrapy.Spider):
    name = 'product-url'
    start_urls = [
        "https://www.sakurapower.com/gasoline-generator/honda-series.html",
        "https://www.sakurapower.com/gasoline-generator/lg-series.html",
        "https://www.sakurapower.com/gasoline-generator/storm-series.html",
        "https://www.sakurapower.com/diesel-generator-29/genmac-diesel.html",
        "https://www.sakurapower.com/diesel-generator-29/diesel-generator-sakura.html",
        "https://www.sakurapower.com/lawn-mower.html",
        "https://www.sakurapower.com/pump/fire-pump.html",
        "https://www.sakurapower.com/pump/water-pump.html",
        "https://www.sakurapower.com/chain-saw.html",
        "https://www.sakurapower.com/spare-parts.html",
        "https://www.sakurapower.com/spare-parts.html?p=2",
        "https://www.sakurapower.com/spare-parts.html?p=3",
        "https://www.sakurapower.com/spare-parts.html?p=4",
        "https://www.sakurapower.com/spare-parts.html?p=5",
    ]

    def start_requests(self):
        for u in self.start_urls:
            yield scrapy.Request(u, callback=self.parse, errback=self.err_back, dont_filter=True)

    def parse(self, response):
        for product_url in response.xpath("//*[@id='page-container']//div[contains(@class,'section-page')]//div[contains(@class,'container')]//div[contains(@class,'category-products')]/div[contains(@class,'item')]/div[contains(@class,'item')]"):
            yield {
                'category_url': response.url,
                'product_url': product_url.xpath("./a/@href").get(),
            }

    def err_back(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
