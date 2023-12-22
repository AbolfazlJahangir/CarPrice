''' Hi there!
The first time you want to run this you should use the 'find_data_cars' function
Only once and when the information is stored in your database
You don't need that function and you can comment it!
'''

import requests
import mysql.connector
from mysql.connector import errorcode
from bs4 import BeautifulSoup
from sklearn import tree


data_cars = []
total_data = []
ranking_cars = {}
x = []
y = []

cnx = mysql.connector.connect(user='', password='', host='', database='')
cursor = cnx.cursor()

# To have a numerical criterion for use the 'DecisionTreeRegressor'
def ranking(): # OK
    url_rank = 'https://caredge.com/ranks/costs/70k/least-expensive#models'
    r_rank = requests.get(url_rank)
    soup_rank = BeautifulSoup(r_rank.text, 'html.parser')

    results_rank = soup_rank.find('table', class_='table table-striped table-bordered table-hover ranks-table').find_all('tr')

    c = 0
    for restult_rank in results_rank:
        c += 1
        if c == 1:
            continue
        else:
            x = restult_rank.text.strip().split('\n')
            price_rank = x[2][1:].replace(',','')
            ranking_cars[x[1].lower()] = int(price_rank)

# Create the table in database
def table(): # OK
    table = '''CREATE TABLE cars(
    name VARCHAR(200),
    model VARCHAR(200),
    year VARCHAR(6),
    price VARCHAR(20),
    mileage VARCHAR(20),
    UNIQUE KEY UniqueCombination (name, model, year, price, mileage)
    )'''

    try:
        cursor.execute(table)
        cnx.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print('This Table already exists!')
        else:
            print('Something wrong about table!')
    else:
        print('Table created!')

# Extraction cars data
def find_data_cars(): # OK
    print('Wait a few minutes...')
    c = 0
    page = 333
    for i in range(1,page+1):
        c += 1
        url = f'https://www.truecar.com/used-cars-for-sale/listings/?page={i}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text,'html.parser')
        results = soup.find_all('li', class_='mt-3 flex grow col-md-6 col-xl-4')

        for result in results:
            name = result.find('span', class_='truncate').text
            model = result.find('div', class_='truncate text-xs').text
            year = result.find('span', class_='vehicle-card-year text-xs').text.strip()
            price = result.find('div', class_='vehicle-card-bottom-pricing-secondary pl-3 lg:pl-2 vehicle-card-bottom-max-50').find('span').text
            mileage = result.find('div', class_='flex w-full justify-between').find('div').text
            
            year = str(year)

            new_price = str()
            price = price[1:]
            part_price = price.split(',')
            for partp in part_price:
                new_price += partp
            price = str(new_price)

            mileage = mileage[:-5].strip()
            mileage = str(mileage.replace(',',''))

            data_car = {
                'name':name.lower(),
                'model':model.lower(),
                'year':year,
                'price':price,
                'mileage':mileage
                        }
            total_data.append(data_car)

            try:
                insert_data = '''INSERT INTO test.cars(name,model,year,price,mileage)
                                VALUES (%s,%s,%s,%s,%s)'''
                full_data = (name.lower(),model.lower(),year,price,mileage)
                cursor.execute(insert_data,full_data)
                cnx.commit()
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    if c == len(total_data):
                        print('Data already exists!')
                else:
                    print('Error: ',err)
    print('Data extraction done!')

ranking()
table()
#find_data_cars() --> # We need to use this function once and after that we have the data in our database

query = '''SELECT * FROM test.cars'''
cursor.execute(query)
result = cursor.fetchall()

# Collecting data in dictionary
for row in result:
    name = row[0]
    model = row[1]
    year = row[2]
    price = row[3]
    mileage = row[4]

    data_car = {
        'name':name,
        'model':model,
        'year':year,
        'price':price,
        'mileage':mileage
                }
    data_cars.append(data_car)

    for car in ranking_cars:
        score = 20000   # The default value for every car
        if car in name:
            score = ranking_cars[car]
            break
    l = [score,int(year),int(mileage)]
    x.append(l)
    y.append([int(price)])

car_name = input('Your car name: ').lower()
car_year = int(input('Year: '))

while True:
    choice_milage = input('1-mile/2-km (1 or 2): ').lower()

    if choice_milage == '2':
        car_milage = int(input('How many KM it used? '))/1.609
        break
    elif choice_milage == '1':
        car_milage = int(input('How many MILE it used? '))
        break
    else:
        print('Please enter (mile or km)')
new_data = [car_name,car_year,car_milage]


for rank in ranking_cars:
    score = 20000
    if rank in new_data[0]:
        score = ranking_cars[rank]
        break
new_data[0] = score


# Using the collected models in DecisionTreeRegressor
clf = tree.DecisionTreeRegressor()
clf = clf.fit(x,y)
answer = clf.predict([new_data])
p = int(answer[0])


cnx.close()
cursor.close()


print(f'The suggested price is {p} dollars.')