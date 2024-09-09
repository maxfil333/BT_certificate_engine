import os
import re
from typing import Literal, Optional


from utils import is_scanned_pdf, extract_text_with_fitz


def text_classifier(text: str) -> Optional[Literal['act', 'conos', 'pi', 'report']]:
    """ takes text, returns 'class_name' or None """

    pi_regex = r'протокол\s{1,5}исследований\s{1,5}\(?испытаний\)?'
    report_regex = r'заключение\s{1,5}о\s{1,5}(?:карантинном\s{1,5})?фитосанитарном\s{1,5}состоянии'
    conos_key_words = ['shipper', 'consignee', 'notify address',
                       'port of loading', 'port of receipt', 'port of delivery', 'port of discharge',
                       'place of receipt', 'particulars declared', 'description of goods',
                       'description of packages', 'bill of lading', 'vessel', 'voyage', 'booking number', 'b/l',
                       'shipper owned', 'shipper\'s load', 'shipper\'s stow', 'weight and seal', 'freight prepaid'
                       'freight charges', 'FCL', 'LCL', 'уведомление о прибытии груза', 'порт погрузки']
    conos_key_words = sorted(conos_key_words, key=lambda x: len(x.split()), reverse=True)
    conos_regex = r'|'.join([re.escape(word) for word in conos_key_words])

    if re.findall(pi_regex, text, flags=re.IGNORECASE):
        return 'pi'
    if re.findall(report_regex, text, flags=re.IGNORECASE):
        return 'report'
    if len(set(re.findall(conos_regex, text, flags=re.IGNORECASE))) >= 3:  # уникальных ключевых слов > 3
        return 'conos'
    print('conos matches:', re.findall(conos_regex, text, flags=re.IGNORECASE))
    return None



