import urllib.request
from bs4 import BeautifulSoup
import re
import time
from forex_python.converter import CurrencyRates

rate = CurrencyRates().get_rate('USD', 'CAD')

pages = ["https://steamcommunity.com/market/search?q=holo+2019#p1_default_desc",
		 "https://steamcommunity.com/market/search?q=holo+2019#p2_default_desc",
		 "https://steamcommunity.com/market/search?q=holo+2019#p3_default_desc",
		 "https://steamcommunity.com/market/search?q=holo+2019#p4_default_desc",
		 "https://steamcommuvnity.com/market/search?q=holo+2019#p5_default_desc",
		 "https://steamcommunity.com/market/search?q=holo+2019#p6_default_desc"
		]

lstStickers = ["Sticker | Tyloo (Holo) | Katowice 2019",
			   "Sticker | Cloud9 (Holo) | Katowice 2019",
			   "Sticker | Natus Vincere (Holo) | Katowice 2019",
			   "Sticker | FaZe Clan (Holo) | Katowice 2019",
			   "Sticker | Astralis (Holo) | Katowice 2019",
			   "Sticker | Tyloo (Holo) | Berlin 2019",
			   "Sticker | Astralis (Holo) | Berlin 2019"
			  ]

for page in pages:
	result = urllib.request.urlopen(page)
	soup = BeautifulSoup(result, 'lxml')

	pricePage = soup.find_all("span", {"class": "market_table_value normal_price"})

	priceRegexUSD = re.findall(r'[\$][0-9]{1,5}[.][0-9]{2}\s\w{3}', str(pricePage))
	del priceRegexUSD[1::2]
	#print(priceRegexUSD)


	priceRegexCDN = re.findall(r'[$](\d+.\d{2})\s\w{3}', str(priceRegexUSD))
	# Changing USD to CDN
	for i in range(10):
		priceRegexCDN[i] = str("{0:.2f}".format(float(priceRegexCDN[i]) * rate))
	# Adding the dollar sign and CDN back to each item
	for i in range(10):
		priceRegexCDN[i] = '$' + str(priceRegexCDN[i]) + ' CDN'

	#print(priceRegexCDN)

	namePage = soup.findAll("span", {"class": "market_listing_item_name"})
	nameRegex = re.findall(r'>([A-Za-z0-9\s|()\/]+)<\/span>', str(namePage))
	#print(nameRegex)

	qtyPage = soup.find_all("span", {"class": "market_listing_num_listings_qty"})
	qtyRegex = re.findall(r'\d+', str(qtyPage))

	del qtyRegex[1::2]
	#print(qtyRegex)

	for i in range(10):
		print('Name: ' + nameRegex[i])
		print('Price (USD): ' + priceRegexUSD[i])
		print('Price (CDN): ' + priceRegexCDN[i])
		print('Quantity: ' + qtyRegex[i] + '\n')

	time.sleep(20)

	# add if statement in for loop to store prices if they are the sticker i want to track prices for
