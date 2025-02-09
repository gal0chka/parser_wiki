import scrapy
import json

class FilmSpider(scrapy.Spider):
    name = 'films'
    film_count = 0
    max_films = 1000
    imdb_api_key = '92685a90'

    def start_requests(self):
        url = 'https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        film_links = response.css('div.mw-category-group ul li a::attr(href)').getall()

        for link in film_links:
            if self.film_count >= self.max_films:
                return

            if not "/wiki/Категория:" in link:
                full_link = response.urljoin(link)
                self.film_count += 1
                yield scrapy.Request(url=full_link, callback=self.parse_film)

        next_page = response.css('a[title="Категория:Фильмы по алфавиту"]:contains("Следующая страница")::attr(href)').get()
        if next_page and self.film_count < self.max_films:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_film(self, response):
        film_name = response.css('th.infobox-above::text').get()
        year = response.xpath('//td[@class="plainlist"]/a/span[@class="dtstart"]/text()').get()
        
        if not year:
            year = response.css('th:contains("Год") + td a::text').get()

        if film_name:
            film_data = {
                'name': film_name,
                'kind': response.css('td.plainlist span[data-wikidata-property-id="P136"] a::attr(title)').getall(),
                'director': response.css('td.plainlist span[data-wikidata-property-id="P57"] a::attr(title)').getall(),
                'country': response.css('td.plainlist span[data-wikidata-property-id="P495"] a::attr(title)').getall(),
                'year': year,
            }
            imdb_url = f"https://www.omdbapi.com/?t={film_name}&apikey={self.imdb_api_key}"
            yield scrapy.Request(url=imdb_url, callback=self.parse_imdb, meta={'film_data': film_data})

    def parse_imdb(self, response):
        film_data = response.meta['film_data']
        imdb_data = json.loads(response.text)
        film_data['imdb_rating'] = imdb_data.get('imdbRating', 'N/A')

        yield film_data
