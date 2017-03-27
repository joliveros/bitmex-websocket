import json


def message_fixtures():
    data = {}

    orderBookL2_data = {}
    with open('./tests/fixtures/order_book_l2_partial_action_message.json')\
            as partial_data:
        orderBookL2_data['partial'] = json.load(partial_data)
    with open('./tests/fixtures/order_book_l2_insert_action_message.json')\
            as insert_data:
        orderBookL2_data['insert'] = json.load(insert_data)
    with open('./tests/fixtures/order_book_l2_delete_action_message.json')\
            as delete_data:
        orderBookL2_data['delete'] = json.load(delete_data)
    with open('./tests/fixtures/order_book_l2_update_action_message.json')\
            as update_data:
        orderBookL2_data['update'] = json.load(update_data)

    data['orderBookL2'] = orderBookL2_data

    instrument_data = {}

    with open('./tests/fixtures/instrument_partial_action_message.json')\
            as partial_data:
        instrument_data['partial'] = json.load(partial_data)
    with open('./tests/fixtures/instrument_update_action_message.json')\
            as update_data:
        instrument_data['update'] = json.load(update_data)

    data['instrument'] = instrument_data

    return data
