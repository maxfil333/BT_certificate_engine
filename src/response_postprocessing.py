import re
import json

from typing import Union, Literal
from win32com.client import CDispatch

from src.logger import logger
from src.utils import switch_to_latin, try_exec
from src.http_connector import cup_http_request


def main_postprocessing(response, connection: Union[None, Literal['http'], CDispatch]) -> str:
    dct = json.loads(response)
    dct['Номера сделок'] = []
    dct['Номера таможенных сделок'] = []
    dct['Номера фсс'] = '%None%'

    if len(dct['Номер коносамента']) < 5:
        dct['Номер коносамента'] = ''

    if dct['Тип документа'] == 'акт':
        # валидация номера акта
        if not re.fullmatch(r'\d{15}', dct['Номер документа'].strip()):
            logger.print(f"! act number {dct['Номер документа']} is not valid !")
            dct['Номер документа'] = 'unrecognized_act'

        # проверка контейнер и коносамент перепутаны
        container_regex = r'[A-ZА-Я]{3}U\s?[0-9]{6}-?[0-9]'
        if dct['Номер коносамента'] and dct['Номера контейнеров'] and len(dct['Номера контейнеров']) == 1:
            if not re.fullmatch(container_regex, dct['Номера контейнеров'][0]):
                logger.print(f"Containers: {dct['Номера контейнеров']}, swap with conos {dct['Номер коносамента']}")
                conos, container = dct['Номер коносамента'], dct['Номера контейнеров'][0]
                dct['Номер коносамента'] = container
                dct['Номера контейнеров'] = [conos]

    if connection and dct['Номер коносамента']:
        conos = dct['Номер коносамента']
        if connection == 'http':
            logger.print('TransactionNumberFromBillOfLading and CustomsTransactionFromBillOfLading search...')
            trans_number = cup_http_request(r'TransactionNumberFromBillOfLading', conos)
            customs_trans = cup_http_request(r'CustomsTransactionFromBillOfLading', conos)
        else:
            trans_number = try_exec(connection.InteractionWithExternalApplications.TransactionNumberFromBillOfLading,
                                    conos)
            customs_trans = try_exec(connection.InteractionWithExternalApplications.CustomsTransactionFromBillOfLading,
                                     conos)
            trans_number = [x.strip() for x in trans_number if x.strip()]
            customs_trans = [x.strip() for x in customs_trans if x.strip()]

        dct['Номера сделок'] = trans_number
        dct['Номера таможенных сделок'] = customs_trans

    # если "Номер коносамента" попал в "Номер документа"
    if connection and dct['Тип документа'] == 'коносамент':
        document = dct['Номер документа']
        if document and not (dct['Номера сделок'] or dct['Номера таможенных сделок']):
            logger.print('Trans..illOfLading and CustomsTrans..illOfLading search with conos and document swap..')
            trans_number = cup_http_request(r'TransactionNumberFromBillOfLading', document)
            customs_trans = cup_http_request(r'CustomsTransactionFromBillOfLading', document)
            if trans_number or customs_trans:  # если так, то надо заполнить Номер коносамента
                dct['Номер коносамента'] = document
                dct['Номера сделок'] = trans_number
                dct['Номера таможенных сделок'] = customs_trans
                logger.print('Коносамент перенесен из "Номера документа" в "Номер коносамента"')

    return json.dumps(dct, ensure_ascii=False, indent=4)


def appendix_postprocessing(response, connection: Union[None, Literal['http'], CDispatch]) -> str:
    dct = json.loads(response)

    fcc_numbers = []
    for pos in dct['documents']:
        doc_numbers = pos["Номера документов"]
        for number in doc_numbers:
            if number not in fcc_numbers:
                fcc_numbers.append(number)

    transaction_numbers = []
    if connection and fcc_numbers:
        logger.print('CustomsTransactionNumberFromBrokerDocument search...')
        for number in fcc_numbers:
            if True:  # try in english
                number_en = switch_to_latin(number)
                if connection == 'http':
                    customs_trans = cup_http_request(r'CustomsTransactionNumberFromBrokerDocument', number_en)
                else:
                    customs_trans = try_exec(
                        connection.InteractionWithExternalApplications.CustomsTransactionNumberFromBrokerDocument,
                        number_en)
            if not customs_trans:  # then try in russian
                number_ru = switch_to_latin(number, reverse=True)
                if number_ru != number_en:
                    if connection == 'http':
                        customs_trans = cup_http_request(r'CustomsTransactionNumberFromBrokerDocument', number_ru)
                    else:
                        customs_trans = try_exec(
                            connection.InteractionWithExternalApplications.CustomsTransactionNumberFromBrokerDocument,
                            number_ru)
            if customs_trans:  # if some result
                transaction_numbers.extend(customs_trans)

    dct['Номера фсс'] = fcc_numbers
    dct['Номера таможенных сделок'] = list(dict.fromkeys(transaction_numbers))

    return json.dumps(dct, ensure_ascii=False, indent=4)


def get_clean_transactions(result: str) -> str:
    dct = json.loads(result)
    deal_regex = r'(.*) (от) (.*)'
    dct['Номера таможенных сделок без даты'] = [re.fullmatch(deal_regex, i).group(1)
                                                for i in dct['Номера таможенных сделок']]
    return json.dumps(dct, ensure_ascii=False, indent=4)


def get_consignee_and_feeder(response: str, connection: Union[None, Literal['http'], CDispatch]) -> str:
    """
    :param response:   json formatted string
    :param connection: connection type
    """
    dct = json.loads(response)
    dct['feeder_ships'], dct['consignees'], dct['consignee_deal_feeder'] = [], [], []
    clean_deals = dct['Номера таможенных сделок без даты']

    func_name = r'UnitDataByTransactionNumber'
    params = r'СудноФидер,Грузополучатель'
    logger.print('feeder and consignee from broker deal search...')

    for deal in clean_deals:
        if connection == 'http':
            feeder_and_consignee_request = cup_http_request(func_name, deal, params)
        else:
            feeder_and_consignee_request = try_exec(
                connection.InteractionWithExternalApplications.UnitDataByTransactionNumber, deal, params
            )
        if isinstance(feeder_and_consignee_request, dict):
            ship = feeder_and_consignee_request.get('СудноФидер', '')
            consignee = feeder_and_consignee_request.get('Грузополучатель', '')
        else:
            ship = ""
            consignee = ""

        dct['feeder_ships'].append(ship)
        dct['consignees'].append(consignee)

    dct['consignee_deal_feeder'] = [f"{c}_{d}_{f}"
                                    for c, d, f in
                                    zip(dct['consignees'], clean_deals, dct['feeder_ships'])]

    dct['consignee_deal_feeder_short'] = [f"{c[:30]}_{d}_{f[:30]}"
                                          for c, d, f in
                                          zip(dct['consignees'], clean_deals, dct['feeder_ships'])]

    return json.dumps(dct, ensure_ascii=False, indent=4)
