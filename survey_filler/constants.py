USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.3497.92 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
]

SURVEY_URL = 'https://www.mcdfoodforthoughts.com/'

PRE_QUESTION_DELAY = (1000, 2000)
ERROR_504_RETRY_DELAY = (10000, 15000)
QUESTION_PRE_ANSWER_DELAY = (1000, 2000)
QUESTION_POST_ANSWER_DELAY = (500, 1000)
CHECKBOX_RETRY_DELAY = (2500, 3500)
NO_QUESTION_DELAY = (5000, 7000)

MAX_TOTAL_504_RETRIES = 8
MAX_CONSECUTIVE_504_RETRIES = 4

MAX_504_BACKOFF_DELAY = 40000

# A series of ChatGPT-generated long answers to the question "Why were you highly satisfied?"
LONG_ANSWERS = [
    'Staff super nice, food tasty, in and out real quick loved it',
    'Place clean, food good, staff cool, awesome time',
    'Fast service, yummy food and a chill vibe. great visit',
    'No order problems, food rocked and staff were friendly',
    'Quick, no mistakes, food awesome',
    'Nice staff, fast service',
    'Quick accurate orders and the food was delish',
    'Clean, fast service and the food was great',
    'Fast, no problems, all was good',
    'Quick, no mistakes, food was great',
    'Everything was fine, no errors, fast service',
    'Nice staff, quick service and tasty food',
    'Clean place, good food, and friendly staff',
    'Fast service, delicious food, and a relaxed vibe',
    'No order issues, staff was friendly, food was on point',
    'Quick and accurate service, tasty food',
    'Staff was cool, service was fast, and the food was really good',
    'Accurate order, quick service, food was delicious',
    'Clean, fast, food was tasty',
    'Fast, no mistakes, nice food',
]

BASE_QUESTION_DATA = {
    'R000005': 1,  # visit type [1 = dined in]

    'R000002': 5,  # overall satisfaction [5 = very satisfied -> 1 = very dissatisfied]

    'R000006': 2,  # where placed order [2 = touch screen]

    'R000053': 1,  # how reciever order [1 = at counter]

    'R000384': 1,  # mcdonalds rewards [1 = yes]

    'R000018': 9,  # cleanliness of toilet [5 = very satisfied -> 1 = very dissatisfied, 9 = n/a]
    'R000020': 5,  # cleanliness of restaurant [5 = very satisfied -> 1 = very dissatisfied]
    'R000011': 5,  # appearance of food [5 = very satisfied -> 1 = very dissatisfied]
    'R000012': 5,  # accuracy of order [5 = very satisfied -> 1 = very dissatisfied]
    'R000009': 5,  # taste of food [5 = very satisfied -> 1 = very dissatisfied]

    'R000016': 5,  # ease of placing order [5 = very satisfied -> 1 = very dissatisfied]
    'R000017': 5,  # speed of service [5 = very satisfied -> 1 = very dissatisfied]
    'R000010': 5,  # temperature of food [5 = very satisfied -> 1 = very dissatisfied]
    'R000019': 5,  # friendliness of staff [5 = very satisfied -> 1 = very dissatisfied]
    'R000008': 5,  # quality of food [5 = very satisfied -> 1 = very dissatisfied]

    'R000021': 5,  # overall value for price [5 = very satisfied -> 1 = very dissatisfied]

    'R000052': 1,  # order accuracy [1 = yes]

    'R000026': 2,  # problem with order [2 = no]

    'S000034': '$LONG_ANSWER$',  # why were you (highly satisfied) [text area]

    ###
    # select items you ordered (multiple choice)
    'R000041': 1,  # fries multi-select
    'R000191': 1,  # double quarter pounder with cheese multi-select

    'R000014': 5,  # temperature of fries (if selected) [5 = very satisfied -> 1 = very dissatisfied]

    'R000307': 5,  # quality of fries (if selected) [5 = very satisfied -> 1 = very dissatisfied]
    'R000256': 5,  # quality of dbl QP with cheese (if selected) [5 = very satisfied -> 1 = very dissatisfied]
    ###

    'R000499': 5,  # affordable menu options [5 = very satisfied -> 1 = very dissatisfied]

    'R000054': 2,  # recognise staff member [2 = no]

    'R000466': 2,  # answer more questions [2 = no]

    'R000383': 2,  # voucher delivery [2 = print]
}
