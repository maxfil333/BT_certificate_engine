import re
from typing import Literal, Optional

from logger import logger


def text_classifier(text: str) -> Optional[Literal['conos', 'pi', 'report']]:
    """ takes text: str, returns 'class_name' or None """

    pi_regex = r'протокол\s{1,5}исследований\s{1,5}\(?испытаний\)?'
    report_regex = r'заключение\s{1,5}о\s{1,5}(?:карантинном\s{1,5})?фитосанитарном\s{1,5}состоянии'
    conos_key_words = ['shipper', 'consignee', 'notify address',
                       'port of loading', 'port of receipt', 'port of delivery', 'port of discharge',
                       'place of receipt', 'particulars declared', 'description of goods',
                       'description of packages', 'bill of lading', 'vessel', 'voyage', 'booking number', 'b/l', 'bl',
                       'shipper owned', 'shipper\'s load', 'shipper\'s stow', 'weight and seal', 'freight prepaid',
                       'freight charges', 'FCL', 'LCL', 'уведомление о прибытии груза', 'порт погрузки']
    conos_key_words = sorted(conos_key_words, key=lambda x: len(x.split()), reverse=True)
    conos_regex = r'|'.join([re.escape(word) for word in conos_key_words])

    if re.findall(pi_regex, text, flags=re.IGNORECASE):
        return 'pi'
    if re.findall(report_regex, text, flags=re.IGNORECASE):
        return 'report'

    conos_matches = re.findall(conos_regex, text, flags=re.IGNORECASE)
    if conos_matches:
        logger.print('conos matches:', conos_matches)
        if len(set(conos_matches)) >= 3:  # уникальных ключевых слов >= 3
            return 'conos'


if __name__ == "__main__":
    print(text_classifier('протокол исследований испытаний'))
    print(text_classifier('заключение о фитосанитарном состоянии'))
    print(text_classifier('BL shipper consignee'))
