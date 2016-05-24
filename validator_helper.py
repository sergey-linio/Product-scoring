import os
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import requests
from PIL import Image
from langdetect import detect, lang_detect_exception
from configobj import ConfigObj
import pickle
import json

from sql import *


def get_score(product_id, engine):
    return MainValidator(prepare_data(product_id, engine), get_params()).get_total_sum(get_weights(product_id, engine))


def prepare_data(product_id, engine):
    text_data = engine.execute(sql_text.format(product_id)).fetchone()
    image_data = engine.execute(sql_image.format(product_id)).fetchone()
    category_data = engine.execute(sql_category.format(product_id)).fetchone()
    negative_data = engine.execute(sql_negative.format(product_id)).fetchone()

    return {
        'text_data': text_data,
        'image_data': image_data,
        'category_data': category_data,
        'negative_data': negative_data,
    }


def get_weights(product_id, engine):
    sqlite3engine = create_engine('sqlite:///test.db')
    for category in engine.execute(sql_weights.format(product_id)).fetchall():
        cat = sqlite3engine.execute(
            'SELECT * FROM category WHERE category.category_id = {}'.format(str(category.id_catalog_category))
        ).fetchone()
        if cat.level == 2:
            return json.loads(cat.scores)


def get_params():

    cfg = ConfigObj('config.ini')
    params = {}

    for section in cfg.keys():

        for key, value in cfg[section].items():

            # TODO: use isinstace()
            if type(value) == type([]):
                params[key] = value
                continue

            if '.' in value:
                params[key] = float(value)
                continue

            params[key] = int(value)

    return params


class BaseValidator(object):
    '''
    Interface of Validators.
    Implements function, which call all functions starts with 'validate_' and
    create dictionary based on their names.
    '''
    def run_tests(self):
        result = {}
        for function in filter(lambda x: x.startswith('validate_'), dir(self)):
            result[function.split('validate_')[1]] = getattr(self, function)()
        return result

    def get_total_sum(self, weights):
        return reduce(
            lambda res, (key, value): res + (weights.get(key, 0) if value and weights else 0),
            self.run_tests().items(),
            0
        )

    @classmethod
    def get_validators_name(self):
        return filter(lambda x: x.startswith('validate_'), dir(self))


class TextValidator(BaseValidator):
    '''

    This class provides validation of product description
    ---------------------------------------------

    Constructor takes following parameters:

        data - result of executing sql_text query: see sql.py for details

        params - dictionary with following keys:

            * title_min_length
            * title_max_length
            * description_min_length
            * bold_min_rate
            * bold_max_rate
            * bullets_min_count
            * bullets_max_count

    '''

    def __init__(self, data, params):
        self.params = params
        self.item_info_text = data

    def _get_words_amount(self):
        soup = BeautifulSoup(self.item_info_text.description, 'html.parser')
        return len(soup.text.replace('\n', '').split(' '))

    def _get_bold_words_amount(self):
        soup = BeautifulSoup(self.item_info_text.description, 'html.parser')
        return len(filter(None, ' '.join(map(lambda x: x.text, soup.select('b'))).split(' ')))

    def _get_bolds_rate(self):
        return float(self._get_bold_words_amount()) / self._get_words_amount()

    def validate_brand_in_title(self):
        """Title contains brand"""
        return self.item_info_text.brand.lower() in self.item_info_text.title.lower()

    def validate_title_length(self):
        """Title between 50 and 60 letters"""
        return self.params['title_min_length'] <= len(self.item_info_text.title) <= self.params['title_max_length']

    def validate_description_length(self):
        """Description longer 150 letters"""
        return self._get_words_amount() >= self.params['description_min_length']

    def validate_bold_rate(self):
        """3 - 5% of description is bold"""
        return self.params['bold_min_rate'] <= self._get_bolds_rate() <= self.params['bold_max_rate']

    def validate_bullets_count(self):
        """Has 5 or 6 bullets"""
        if self.item_info_text.short_description:
            return self.params['bullets_min_count'] <= self.item_info_text.short_description.count('<li>') <= self.params['bullets_max_count']
        else:
            print 'No short desc for {}'.format(self.item_info_text.sku)
            return False


class ImageValidator(BaseValidator):
    '''

    This class provides validation of product images
    ---------------------------------------------

    Constructor takes following parameters:

        data - result of executing sql_image query: see sql.py for details

        params - dictionary with following keys:

            * image_min_dimensions

    '''

    def __init__(self, data, params):
        self.params = params
        self.item_info_image = data

        self.image_params = []
        url_tmpl = 'https://media.linio.com.mx/p/{brand_url_key}-{catalog_id}-{number}.jpg'
        for i in xrange(self.item_info_image.image_count):
            self.image_params.append(
                self._get_image_params(
                    url_tmpl.format(
                        brand_url_key=self.item_info_image.url_key,
                        catalog_id=str(self.item_info_image.id_catalog_config)[::-1],
                        number=i+1,
                    )
                )
            )

    def _get_image_params(self, url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 404:
                return {
                    'height': 0,
                    'width': 0,
                }
            img = Image.open(response.raw)
            return {
                'height': img.size[0],
                'width': img.size[1],
            }
        except:
            print '{} returned Exception {}'.format(url, Exception.message)
            raise

    def validate_image_count_2(self):
        """Has 2 images"""
        return self.item_info_image.image_count == 2

    def validate_image_count_m_2(self):
        """Has more than 2 images"""
        return self.item_info_image.image_count > 2

    def validate_image_dimensions(self):
        """More than 800px"""
        return reduce(
            lambda res, x: res and x['height'] >= self.params['image_min_dimensions']
                               and x['width'] >= self.params['image_min_dimensions'],
            self.image_params,
            True
        )


class CategoryValidator(BaseValidator):
    '''

    This class provides validation of product categories
    ---------------------------------------------

    Constructor takes following parameters:

        data - result of executing sql_category query: see sql.py for details

    '''

    def __init__(self, data):
        self.item_info_cat = data

    def validate_category_level_1(self):
        """Has category level 1"""
        return self.item_info_cat.category_count >= 1

    def validate_category_level_2(self):
        """Has category level 2"""
        return self.item_info_cat.category_count >= 2

    def validate_category_level_3(self):
        """Has category level 3"""
        return self.item_info_cat.category_count >= 3

    def validate_category_level_4(self):
        """Has category level 4"""
        return self.item_info_cat.category_count >= 4


class NegativeValidator(BaseValidator):
    '''

    This class provides validation of product images
    ---------------------------------------------

    Constructor takes following parameters:

        data - result of executing sql_negative query: see sql.py for details

        params - dictionary with following keys:

            * bold_overflow_rate
            * common_brands
            * title_overflow_length

    '''

    def __init__(self, data, params):
        self.params = params
        self.item_info_negative = data

    def _get_words_amount(self):
        soup = BeautifulSoup(self.item_info_negative.description, 'html.parser')
        return len(soup.text.replace('\n', '').split(' '))

    def _get_bold_words_amount(self):
        soup = BeautifulSoup(self.item_info_negative.description, 'html.parser')
        return len(filter(None, ' '.join(map(lambda x: x.text, soup.select('b'))).split(' ')))

    def validate_overflow_bold_rate(self):
        """More than 7% is bold"""
        return float(self._get_words_amount()) / self._get_words_amount() >= self.params['bold_overflow_rate']

    def validate_overflow_title_length(self):
        """Title more than 100 letters"""
        return len(self.item_info_negative.title) >= self.params['title_overflow_length']

    def validate_language_english(self):
        """Content in English"""
        try:
            language = detect(self.item_info_negative.description)
            return language == 'en'
        except lang_detect_exception.LangDetectException as exc:
            print '{} returned LangDetectException "{}"'.format(self.item_info_negative.sku, exc.message)
            return False

    def validate_has_common_brand(self):
        """Common brand"""
        return self.item_info_negative.brand in self.params['common_brands']

    def validate_incorrect_categorization(self):
        """Incorrect categorization"""
        return False

    def validate_duplicated_content(self):
        """Contains duplicated content"""
        return False


class MainValidator(TextValidator, ImageValidator, CategoryValidator, NegativeValidator):

    def __init__(self, data, params):
        self.params = params
        TextValidator.__init__(self, data['text_data'], params)
        ImageValidator.__init__(self, data['image_data'], params)
        NegativeValidator.__init__(self, data['negative_data'], params)
        CategoryValidator.__init__(self, data['category_data'])
