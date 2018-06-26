from splinter import Browser
from selenium import webdriver
import pandas as pd
from datetime import datetime as DateTime, timedelta as TimeDelta
import time
import random
import os
import threading


def get_browser(proxy):
    print("Browser proxy:", proxy)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % proxy)

    browser = Browser('chrome', options=chrome_options, incognito=True)
    browser.driver.set_window_size(800, 600)
    browser.cookies.delete()

    return browser


def search(browser, params):
    print("Search:", params)

    browser.visit('https://www.cityjet.com/')
    time.sleep(DELAYED*(1+random.random()))

    try:
        from_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[1]/div[1]/div/input'
        search_bar = browser.find_by_xpath(from_bar_xpath)
        search_bar.fill(params['flight_from'])

        from_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[1]/div[1]/div/div[2]/ul/li'
        search_bar = browser.find_by_xpath(from_bar_xpath)
        search_bar.click()

        time.sleep(DELAYED*(1+random.random()))

        to_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[1]/div[2]/div/input'
        search_bar = browser.find_by_xpath(to_bar_xpath)
        search_bar.fill(params['flight_to'])

        to_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[1]/div[2]/div/div[2]/ul/li'
        search_bar = browser.find_by_xpath(to_bar_xpath)
        search_bar.click()

        time.sleep(DELAYED*(1+random.random()))

        date_from_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[2]/div[1]/input'
        search_bar = browser.find_by_xpath(date_from_bar_xpath)
        search_bar.fill(params['date_from'])

        time.sleep(DELAYED*(1+random.random()))

        date_to_bar_xpath = '//*[@id="book-flight"]/fieldset[2]/div[2]/div[2]/input'
        search_bar = browser.find_by_xpath(date_to_bar_xpath)
        search_bar.fill(params['date_to'])

        time.sleep(DELAYED*(1+random.random()))

        select_bar_xpath = '//*[@id="book-flight"]/fieldset[4]/div[1]/select/option[1]'
        search_bar = browser.find_by_xpath(select_bar_xpath)
        search_bar.click()

        time.sleep(DELAYED*(1+random.random()))

        search_button_xpath = '//*[@id="book-flight"]/div[1]/a'
        search_button = browser.find_by_xpath(search_button_xpath)
        search_button.click()

        time.sleep(DELAYED*(1+random.random()))

        return browser

    except:
        print("search: fill form and submit except", params)
        raise


def check_result(browser):
    search_results_xpath = '//*[@id="footer-outer"]/div/div[3]/div[2]/div[1]/div[1]/div[1]/ul/li[1]/a'
    search_results = browser.find_by_xpath(search_results_xpath)
    if search_results.value == '' or search_results['href'] == '':
        print('Search Result is Empty', params)
        raise


def parse_result(browser, params):
    scraped_data = []

    try:
        with browser.get_iframe('pass-data-iframe') as iframe:

            # for OUTBOUND
            xflights = '//*[@id="fpow_avail_tb1"]/tbody/tr'
            flights = iframe.find_by_xpath(xflights)
            xdest = '//*[@id="si_outbound"]/p[1]'
            dest = flights.find_by_xpath(xdest)
            #print("[{}]".format(dest.value))
            scraped_data += parse_result_flights(flights, dest.value, params['flight_from'], params['flight_to'], params['date_from'])

            # for RETURN
            xflights = '//*[@id="fpow_avail_tb2"]/tbody/tr'
            flights = iframe.find_by_xpath(xflights)
            xdest = '//*[@id="si_return"]/p[1]'
            dest = flights.find_by_xpath(xdest)
            #print("[{}]".format(dest.value))
            scraped_data += parse_result_flights(flights, dest.value, params['flight_to'], params['flight_from'], params['date_to'])

        #print(scraped_data)

        return scraped_data

    except NotImplementedError as err:
        print("parse_result except: NotImplementedError: " + err, params)
        raise
    except:
        print("parse_result except", params)
        raise


def parse_result_flights(flights, dest, flight_from, flight_to, date_from):
    scraped_data_flights = []

    for flightIdx, flight in enumerate(flights):
        #print("Flight: ", flightIdx)
        blocks = flight.find_by_css('td[class="ff_bgrd1"]')
        scraped_detail = []
        for blockIdx, block in enumerate(blocks):
            xdetails = 'td[class="label"]'
            details = block.find_by_css(xdetails)
            for detailIdx, detail in enumerate(details):
                #print("Detail1: ", detailIdx, detail.value.replace('\n', ' '))
                val = detail.value.replace('\n', ' ').split(' ')
                if len(val) == 2:
                    scraped_detail.append(val[1])
                else:
                    scraped_detail.append('')

        xdetails = 'span[class="nowrap fpow_span_price"]'
        details = flight.find_by_css(xdetails)
        scraped_prices = []
        for detailIdx, detail in enumerate(details):
            #print("Detail All Prices: ", detailIdx, detail.value)
            scraped_prices.append(detail.value)

        blocks = flight.find_by_css('td[class="ff_bgrd2 fpow_bgrd2"]')
        scraped_price_value = parse_result_price(flight, 'VALUE')
        scraped_price_flex = parse_result_price(flight, 'FLEX')
        scraped_price_premium = parse_result_price(flight, 'PREMIUM')

        # clean, format, check error on data

        if scraped_detail and scraped_prices:
            scr_flights = [
                    dest,
                    (DateTime.today()).strftime('%d/%m/%Y %H:%M:%S'),
                    flight_from,
                    flight_to,
                    date_from
                ]
            scr_flights.extend(scraped_detail)
            scr_flights.extend([
                    scraped_prices,
                    scraped_price_value,
                    scraped_price_flex,
                    scraped_price_premium
                ])

            scraped_data_flights.append(scr_flights)

    return scraped_data_flights


def parse_result_price(flight, price_type):
    blocks = flight.find_by_css('td[class="ff_bgrd2 fpow_bgrd2 {}"]'.format(price_type))
    scraped_price = ''
    for blockIdx, block in enumerate(blocks):
        details = block.find_by_css('span[class="nowrap fpow_span_price"]')
        for detailIdx, detail in enumerate(details):
            scraped_price = detail.value

    return scraped_price


def save_result_init(scraped_csv_file):
    df = pd.DataFrame(data=[], columns=["Title", "Scraped At", "From", "To", "Date", "Departs", "Arrives", "Duration", "Stop(s)", "Flight", "All prices", "CityValue", "CityFlex", "CityPremium"])

    if os.path.isfile(scraped_csv_file):
        os.remove(scraped_csv_file)

    df.to_csv(scraped_csv_file, index=False)


def save_result(scraped_data, scraped_csv_file):
    df = pd.DataFrame(data=scraped_data)
    df.to_csv(scraped_csv_file, mode='a', index=False, header=False)
    print(df)


def close_browser(browser):
    browser.quit()


def process_trip(proxy, scraped_csv_file, params):
    formated_params = {
            'flight_from': params[0],
            'flight_to': params[1],
            'day_from': params[2],
            'day_to': params[3],
            'date_from': (DateTime.today() + TimeDelta(days=params[2])).strftime('%d/%m/%Y'),
            'date_to': (DateTime.today() + TimeDelta(days=params[3])).strftime('%d/%m/%Y'),
        }

    try:
        browser = get_browser(proxy)
        browser = search(browser, formated_params)
        check_result(browser)
        scraped_data = parse_result(browser, formated_params)
        save_result(scraped_data, scraped_csv_file)
        close_browser(browser)

        print(["SUCCESS", proxy, scraped_csv_file, formated_params])

    except:
        print("process_trip except")
        close_browser(browser)
        print(["FAILLED", proxy, scraped_csv_file, formated_params])


if __name__ == '__main__':
    DELAYED = 2
    thread_count = 2
    scraped_csv_file = "Result_scraped.csv"
    proxies = [
            "66.70.147.196:3128",
            "178.32.181.66:3128",
            "54.39.46.86:3128",
            "54.39.46.90:3128",
            "5.189.135.153:8888"
        ]
    proxies = random.sample(proxies, len(proxies))

    # params
    plus_day_from = 16
    plus_day_to = 24
    params = [
            ['London', 'Amsterdam', plus_day_from, plus_day_to],
            ['London', 'Dublin', plus_day_from, plus_day_to],
            ['London', 'Florence', plus_day_from, plus_day_to],
            ['Dublin', 'Florence', plus_day_from, plus_day_to],
            ['Manchester', 'Amsterdam', plus_day_from, plus_day_to],
            ['Newcastle', 'Amsterdam', plus_day_from, plus_day_to],
            ['London', 'Dublin', plus_day_from, plus_day_to],
        ]

    save_result_init(scraped_csv_file)

    threads = []
    for paramIdx, param in enumerate(params):
        t = threading.Thread(target=process_trip, args=(proxies[paramIdx%len(proxies)], scraped_csv_file, param,))
        threads.append(t)
        t.start()
        while(len(threads)>=thread_count):
            time.sleep(3)
            threads = list(filter(lambda t : t.isAlive() == True, threads))
            #print("Sleep", len(threads))
            print('.')

    for t in threads:
        t.join()
        #print("Thread join")

    print("End Process")
