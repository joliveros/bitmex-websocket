import json


def message_fixtures():
    data = {}
    data['orderBookL2'] = {}
    with open('./tests/fixtures/order_book_l2_partial_action_message.json')\
            as partial_data:
        data['orderBookL2']['partial'] = json.load(partial_data)
    with open('./tests/fixtures/order_book_l2_insert_action_message.json')\
            as insert_data:
        data['orderBookL2']['insert'] = json.load(insert_data)
    with open('./tests/fixtures/order_book_l2_delete_action_message.json')\
            as delete_data:
        data['orderBookL2']['delete'] = json.load(delete_data)
    with open('./tests/fixtures/order_book_l2_update_action_message.json')\
            as update_data:
        data['orderBookL2']['update'] = json.load(update_data)

    return data
