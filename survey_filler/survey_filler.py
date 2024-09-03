import logging
import os
import random
import re
from datetime import datetime

from playwright.async_api import Error, Page, async_playwright
from playwright_stealth import stealth_async

from . import constants
from .extracted_voucher import ExtractedVoucher


def generate_code_question_data(receipt_code: str, price: str) -> dict[str, str]:
    code_parts = receipt_code.split('-')
    price_parts = price.split('.')

    return {
        'CN1': code_parts[0],
        'CN2': code_parts[1],
        'CN3': code_parts[2],
        'AmountSpent1': price_parts[0],
        'AmountSpent2': price_parts[1],
    }


def get_delay(delay_range: tuple[int, int]) -> int:
    return random.randint(*delay_range)


def choose_random_user_agent():
    return random.choice(constants.USER_AGENTS)


def choose_random_long_answer():
    return random.choice(constants.LONG_ANSWERS)


async def get_playwright_context(p, browser_options=None, user_agent=None):
    """
    Sets up Playwright context with headless browser and optional customizations.

    Args:
        p (async_playwright.async_playwright.AsyncPlaywright): Playwright instance.
        browser_options (dict, optional): Optional configuration options for Playwright browser launch.
        user_agent (str, optional): Optional user agent string for the browser.

    Returns:
        async_playwright.chromium.ChromiumContext: Playwright context object.
    """
    headless = bool(os.getenv('SURVEY_BROWSER_HEADLESS', False))
    browser_options = browser_options or {}
    browser = await p.firefox.launch(headless=headless, slow_mo=10, timeout=0, **browser_options)
    context = await browser.new_context(user_agent=user_agent, viewport={'width': 1280, 'height': 720})

    # Disable webdriver detection
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', false);")

    return context


class SurveyFiller:
    question_data: dict[str, str | int]
    seen_questions: set[str]

    has_504_error: bool = False
    error_504_retries: int = 0
    error_504_consecutive_retries: int = 0

    found_delivery_question: bool = False

    def __init__(self, question_data: dict[str, str | int], receipt_code: str, price: str, logger=None):
        self.seen_questions = set()
        self.question_data = question_data
        self.question_data.update(generate_code_question_data(receipt_code, price))
        self.logger = logger

    def log(self, message, level=logging.INFO):
        if self.logger:
            self.logger.log(level, message)
        else:
            print(message)

    def log_progress(self):
        progress = self.get_progress()
        message = f'PROGRESS_UPDATE={progress * 100:.1f}'
        self.log(message)

    def handle_page_response(self, response):
        if response.status == 504:
            self.has_504_error = True
        else:
            self.error_504_consecutive_retries = 0

    def get_progress(self):
        progress = len(self.seen_questions) / float(len(self.question_data))
        # TODO: maybe add more info to a progress report (i.e. stage or something)
        return progress

    async def fill_survey(self, context) -> ExtractedVoucher:
        page = await context.new_page()
        await stealth_async(page)
        page.on('response', self.handle_page_response)

        await page.goto(constants.SURVEY_URL)
        await page.wait_for_timeout(get_delay(constants.PRE_QUESTION_DELAY))
        await page.click('id=NextButton')

        await self.handle_survey_loop(page)

        voucher: ExtractedVoucher = await self.extract_voucher_code(page)

        await page.close()

        return voucher

    async def handle_survey_loop(self, page: Page):
        while True:
            if self.found_delivery_question:
                self.log('Found delivery question. Exiting.')
                break

            await page.wait_for_timeout(get_delay(constants.PRE_QUESTION_DELAY))

            page_questions = await self.retrieve_page_questions(page)

            for question in page_questions:
                await self.answer_question(question, page)

            progress = self.get_progress()
            self.log(f'Seen {len(self.seen_questions)} / {len(self.question_data)} questions. [{progress * 100:.0f}%]')
            self.log_progress()

            await page.mouse.move(random.randint(0, 1280), random.randint(0, 720), steps=25)
            await page.click('id=NextButton')

    async def retrieve_page_questions(self, page: Page):
        found_questions = False
        page_questions = set()

        while not found_questions:
            question_elements = await page.query_selector_all('[type=checkbox],[type=radio],[type=text],textarea')
            page_questions = {await q.get_attribute('name') for q in question_elements}

            questions_found = len(page_questions)
            if questions_found == 0:
                result = await self.handle_no_questions_found(page)
                if not result:
                    self.abandon_survey()
                continue

            found_questions = True
            self.has_504_error = False

        return page_questions

    async def answer_question(self, question_id, page):
        """
        Answers a specific question based on the provided name and form data.

        Args:
            question_id (str): Name attribute of the question element.
            page (async_playwright.page.Page): Playwright page object.
        """
        answer = self.question_data.get(question_id)

        if answer is None:
            self.log(f"No answer found for question '{question_id}'. Skipping.")
            return

        await page.wait_for_timeout(get_delay(constants.QUESTION_PRE_ANSWER_DELAY))

        if question_id == 'R000383':
            self.log('Found delivery question!')
            self.found_delivery_question = True

        is_text_question = question_id[0] == 'S' or question_id in ['CN1', 'CN2', 'CN3', 'AmountSpent1', 'AmountSpent2']

        # Identify element based on question name and answer value
        selector = f'[name="{question_id}"]' if is_text_question \
            else f'[type="radio"][name="{question_id}"][value="{answer}"],[type="checkbox"][name="{question_id}"][value="{answer}"]'

        element = await page.query_selector(selector)

        if not element:
            self.log(f"Element '{selector}' not found for question '{question_id}'. Skipping.")
            self.seen_questions.add(question_id)
            await page.wait_for_timeout(get_delay(constants.QUESTION_POST_ANSWER_DELAY))
            return

        if is_text_question:
            await self.answer_text_question(element, answer, page)
            self.seen_questions.add(question_id)
            await page.wait_for_timeout(get_delay(constants.QUESTION_POST_ANSWER_DELAY))
            return

        await self.answer_multiple_choice_question(element, answer, page)
        self.seen_questions.add(question_id)
        await page.wait_for_timeout(get_delay(constants.QUESTION_POST_ANSWER_DELAY))

    async def answer_text_question(self, element, answer, page):
        answer = answer.replace('$LONG_ANSWER$', choose_random_long_answer())

        element_id = await element.get_attribute('id')
        await element.fill(answer)

        self.log(f"Answered text question '{element_id}' with '{answer}'.")

    async def answer_multiple_choice_question(self, element, answer, page):
        element_id = await element.get_attribute('id')
        try:
            await element.check(force=True)
            self.log(f"Answered multiple choice question '{element_id}' with '{answer}'.")
        except Error:
            self.log(f"Error answering multiple choice question '{element_id}' with '{answer}'.", level=logging.WARNING)
            try:
                await page.wait_for_timeout(get_delay(constants.CHECKBOX_RETRY_DELAY))
                await element.check(force=True)
                self.log(f"Retried multiple choice question '{element_id}' with '{answer}'.")
            except Error:
                self.log(f"Failed to retry multiple choice question '{element_id}' with '{answer}'.",
                         level=logging.WARNING)
                return

    async def handle_no_questions_found(self, page) -> bool:
        """
        Handles the case where no questions are found on the survey page.

        Args:
            page (async_playwright.page.Page): Playwright page object.

        Returns:
            bool: True if the survey should be retried, False if the survey should be abandoned.
        """

        if not self.has_504_error:
            self.log("No questions found. Waiting and retrying...")
            await page.wait_for_timeout(get_delay(constants.NO_QUESTION_DELAY))
            return True

        # We have a 504 error!
        self.error_504_retries += 1
        self.error_504_consecutive_retries += 1

        if self.error_504_consecutive_retries >= constants.MAX_CONSECUTIVE_504_RETRIES:
            self.log("Too many consecutive 504 errors. Exiting.")
            return False

        if self.error_504_retries >= constants.MAX_TOTAL_504_RETRIES:
            self.log('Too many 504 errors. Exiting.')
            return False

        # Calculate exponential backoff delay - increase delay with each 504 error
        backoff_delay = min(constants.MAX_504_BACKOFF_DELAY,
                            2 ** self.error_504_retries * 1000 + random.randint(0, 1000))

        self.log(f'504 error detected. ({self.error_504_retries}/{constants.MAX_TOTAL_504_RETRIES}) total, '
                 f'({self.error_504_consecutive_retries}/{constants.MAX_CONSECUTIVE_504_RETRIES}) consecutive. '
                 f'Waiting {backoff_delay / 1000:.2f} seconds...')

        await page.wait_for_timeout(backoff_delay)
        url = page.url
        await page.goto(url)
        await page.wait_for_timeout(get_delay(constants.ERROR_504_RETRY_DELAY))
        return True

    def abandon_survey(self):
        self.log("Abandoning survey due to repeated errors.", level=logging.ERROR)
        exit(1)

    async def extract_voucher_code(self, page: Page):
        self.log('Extracting voucher code...')

        try:
            await page.wait_for_load_state('load', timeout=15_000)
        except TimeoutError:
            self.log('Page load timeout. Continuing anyway.', level=logging.WARNING)
        except Exception as e:
            self.log(f'Error waiting for page load: {e}. Continuing anyway, after a short delay.',
                     level=logging.WARNING)
            await page.wait_for_timeout(10_000)

        # save webpage as html (as backup)
        try:
            page_content = await page.content()
            file_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            with open(f'data/saved_pages/voucher_page_{file_timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(page_content)

            self.log('Page saved as HTML.')
        except Exception as e:
            self.log(f'Error saving page as HTML: {e}', level=logging.WARNING)

        # extract voucher code
        coupon_parent = await page.query_selector('id=CouponQRImage')
        if not coupon_parent:
            self.log('Voucher not found. Waiting 60 seconds to allow for possible human interaction.',
                     level=logging.WARNING)
            await page.wait_for_timeout(60_000)

        coupon_parent = await page.query_selector('id=CouponQRImage')
        coupon = await coupon_parent.query_selector('img')
        coupon_qr_src = await coupon.get_attribute('src')
        coupon_code = await coupon.get_attribute('alt')
        coupon_expiry = await (await page.query_selector('id=ExpiryDate')).inner_text()

        self.log(f'Voucher extracted: {coupon_code} (expires {coupon_expiry}). QR code: {coupon_qr_src}')

        # check if voucher is valid
        pattern = r'[A-Z0-9]{12}'
        valid = True
        if not re.match(pattern, coupon_code):
            self.log(f'Invalid voucher code: {coupon_code}. Attempting to extract from QR code.', level=logging.WARNING)

            code_match = re.search(r'D=([A-Z0-9]{12})&', coupon_qr_src)
            coupon_code = code_match.group(1) if code_match else coupon_code
            if not re.match(pattern, coupon_code):
                self.log('Failed to extract valid voucher code from QR code. Providing raw data instead.',
                         level=logging.WARNING)
                valid = False

        parsed_expiry = datetime.strptime(coupon_expiry, '%d/%m/%Y')

        voucher = ExtractedVoucher(coupon_code, parsed_expiry, coupon_qr_src if not valid else None)
        return voucher


async def start(survey_filler: SurveyFiller) -> ExtractedVoucher | None:
    voucher: ExtractedVoucher | None = None
    try:
        async with async_playwright() as p:
            context = await get_playwright_context(p, user_agent=choose_random_user_agent())
            voucher = await survey_filler.fill_survey(context)
            await context.close()
    except NotImplementedError as e:
        survey_filler.log(f"Error during browser setup: {e}. Check browser configuration and compatibility.",
                          level=logging.ERROR)
        # Handle the exception appropriately (e.g., log, retry, or notify)
    except Exception as e:
        survey_filler.log(f"Unexpected error: {e}", level=logging.ERROR)
        # Handle other potential exceptions
    finally:
        return voucher
