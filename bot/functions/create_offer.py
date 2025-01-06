import requests

async def create_offer_url(pil_id: str, pil_size: int, pil_count: int, price: int, full_price: int) -> str:
    offer_url=requests.post("https://api.monobank.ua/personal/checkout/order",
        json={   
            "order_ref": pil_id,
            "amount": full_price,
            "count": pil_count,
            "products": [
                {
                    "name": f"Кастомна подушка Розмір: {pil_size} см",
                    "cnt": pil_count,
                    "price": price,
                    "product_img_src": f"http://3059103.as563747.web.hosting-test.net/data/preview_pils/{pil_id}.png"
                }
            ],
            "dlv_method_list": [
                "np_brnm",
                "courier",
                "np_box"
            ],
            "payment_method_list": [
                "card"
            ],
            "callback_url": f"https://t.me/constructor_pillow_bot?start=paid_order_{pil_id}",
            "return_url": "https://t.me/constructor_pillow_bot"
        },
        headers={'X-Token':'mQn21CdkRQZUhhK3gomr6wg'}
    ).json()
    print(offer_url)

    return offer_url['result']['redirect_url']