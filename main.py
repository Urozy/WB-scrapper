from fastapi import FastAPI
import requests
import time
import json
from fake_useragent import UserAgent

app = FastAPI()

def get_wildberries_data(search_query='холодильник'):
    # Генерируем случайный User-Agent
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': 'https://www.wildberries.ru/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    # Правильные параметры запроса
    params = {
        'query': search_query,
        'resultset': 'catalog',
        'sort': 'popular',
        'page': 1,
        'appType': 1,
        'curr': 'rub',
        'dest': -1257786,
        'regions': '80,64,38,4,115,83,33,68,70,69,30,86,75,40,1,66,48,110,22,31',
        'spp': 0,
        'couponsGeo': '12,7,3,21'
    }

    # Список доступных API-хостов Wildberries
    api_hosts = [
        'https://search.wb.ru',
        'https://search.wildberries.ru',
        'https://search-1.wildberries.ru'
    ]

    for host in api_hosts:
        try:
            api_url = f'{host}/exactmatch/ru/common/v4/search'

            print(f"Пробуем хост: {host}...")
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"Ошибка {response.status_code}, пробуем следующий хост...")
                continue

            data = response.json()

            # Проверяем наличие данных
            if not data.get('data', {}).get('products'):
                print("Нет данных о товарах в ответе, пробуем следующий хост...")
                continue

            products = data['data']['products']
            result = []

            for product in products:
                result.append({
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'brand': product.get('brand'),
                    'price': product.get('priceU') / 100 if product.get('priceU') else None,
                    'sale_price': product.get('salePriceU') / 100 if product.get('salePriceU') else None,
                    'rating': product.get('rating'),
                    'feedbacks': product.get('feedbacks'),
                    'link': f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx",
                    'time': time.strftime('%Y-%m-%d %H:%M:%S')
                })

            return {
                'metadata': {
                    'source': host,
                    'query': search_query,
                    'timestamp': int(time.time()),
                    'results': len(result),
                    'status': 'success'
                },
                'products': result
            }

        except Exception as e:
            print(f"Ошибка при запросе к {host}: {str(e)}")
            continue

    return {
        'metadata': {
            'status': 'error',
            'message': 'Не удалось получить данные ни с одного API-хоста'
        },
        'products': []
    }


def save_data(data, filename='wildberries_data.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные успешно сохранены в {filename}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла: {str(e)}")
        return False

@app.post("/scrape")
async def scrape_wildberries(search_query: str = "холодильник"):
    data = get_wildberries_data(search_query)
    if data['metadata']['status'] == 'success':
        save_data(data)
    return data

if __name__ == '__main__':
    # Получаем данные
    # data = get_wildberries_data()
    #
    # # Сохраняем в файл
    # if data['metadata']['status'] == 'success':
    #     save_data(data)
    #
    #     # Выводим пример данных
    #     print("\nПримеры найденных товаров:")
    #     for product in data['products'][:3]:  # Первые 3 товара
    #         print(f"{product['brand']} - {product['name']}")
    #         print(f"Цена: {product['price']} руб. (со скидкой: {product['sale_price']} руб.)")
    #         print(f"Отзывов: {product['feedbacks']}, Рейтинг: {product['rating']}")
    #         print(f"Ссылка: {product['link']}\n")
    # else:
    #     print("Не удалось получить данные. Попробуйте позже или измените параметры запроса.")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)