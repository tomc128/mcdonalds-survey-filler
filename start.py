import asyncio
import random
from datetime import datetime, timedelta

import survey_filler.constants as constants
from generate_code import generate_code
from survey_filler.survey_filler import SurveyFiller, start

store_id = 155  # random store
purchase_date = datetime(2024, 9, 1, 13, 47, 52)  # random date
order_id = random.randint(0, 99)


print(f'Generating code for store {store_id} at {purchase_date} with order ID {order_id}')

code = generate_code(store_id, order_id, purchase_date)
print(f'Using code: {code}')

filler = SurveyFiller(constants.BASE_QUESTION_DATA, code, '2.99')

asyncio.run(start(filler))
