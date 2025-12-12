"""Генератор XML деклараций по форматам ФНС."""

from typing import Literal
from datetime import datetime
from lxml import etree
import os


class DeclarationXMLGenerator:
    """Генератор XML деклараций по форматам ФНС."""
    
    
    FNS_NAMESPACE = "http://www.nalog.ru/declaration"
    FNS_PREFIX = "nd"
    
    @staticmethod
    def _format_amount(amount: float) -> str:
        """Форматирование суммы для XML (2 знака после запятой)."""
        return f"{amount:.2f}"
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """Форматирование даты для XML (YYYY-MM-DD)."""
        return date_str
    
    @staticmethod
    def _get_period_code(period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"]) -> str:
        """Получение кода периода для ФНС."""
        period_map = {
            "Q1": "21",  # 1 квартал
            "Q2": "22",  # 2 квартал
            "Q3": "23",  # 3 квартал
            "Q4": "31",  # 4 квартал
            "YEAR": "34"  # Год
        }
        return period_map.get(period, "21")
    
    @staticmethod
    def generate_usn_xml(
        inn: str,
        period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"],
        year: int,
        income: float,
        expenses: float,
        tax_rate: Literal[6, 15]
    ) -> str:
        """
        Генерация XML для УСН (КНД 1152017).
        
        Формат: Декларация по налогу, уплачиваемому в связи с применением УСН
        Версия формата: 5.05
        """
        
        nsmap = {DeclarationXMLGenerator.FNS_PREFIX: DeclarationXMLGenerator.FNS_NAMESPACE}
        root = etree.Element(
            f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Файл",
            nsmap=nsmap
        )
        root.set("ВерсияФормата", "5.05")
        root.set("ИдФайл", f"DECL_{inn}_{year}_{period}")
        
        # Титульный лист
        title_page = etree.SubElement(root, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Документ")
        title_page.set("КНД", "1152017")
        title_page.set("НаимДок", "Декларация по налогу, уплачиваемому в связи с применением УСН")
        
        # Сведения о налогоплательщике
        taxpayer = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СвНП")
        inn_elem = etree.SubElement(taxpayer, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}ИННЮЛ")
        inn_elem.text = inn
        
        # Период
        period_elem = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Период")
        period_elem.set("Год", str(year))
        period_elem.set("Код", DeclarationXMLGenerator._get_period_code(period))
        
        # Раздел 1 - Сумма налога к уплате
        section1 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1")
        
        if tax_rate == 6:
            # УСН "Доходы" 6%
            subsection_1_1 = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1.1")
            tax_amount = income * 0.06
            tax_elem = etree.SubElement(subsection_1_1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНалУпл")
            tax_elem.text = DeclarationXMLGenerator._format_amount(tax_amount)
        else:
            # УСН "Доходы минус расходы" 15%
            subsection_1_2 = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1.2")
            tax_base = income - expenses
            if tax_base > 0:
                tax_amount = tax_base * 0.15
            else:
                tax_amount = 0.0
            tax_elem = etree.SubElement(subsection_1_2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНалУпл")
            tax_elem.text = DeclarationXMLGenerator._format_amount(tax_amount)
        
        # Раздел 2 - Расчет налоговой базы и суммы налога
        section2 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел2")
        
        if tax_rate == 6:
            # Раздел 2.1.1 - Доходы
            subsection_2_1_1 = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел2.1.1")
            income_elem = etree.SubElement(subsection_2_1_1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумДох")
            income_elem.text = DeclarationXMLGenerator._format_amount(income)
        else:
            # Раздел 2.2 - Доходы и расходы
            subsection_2_2 = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел2.2")
            income_elem = etree.SubElement(subsection_2_2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумДох")
            income_elem.text = DeclarationXMLGenerator._format_amount(income)
            expenses_elem = etree.SubElement(subsection_2_2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумРасх")
            expenses_elem.text = DeclarationXMLGenerator._format_amount(expenses)
        
        # Формирование XML строки
        xml_bytes = etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )
        return xml_bytes.decode("UTF-8")
    
    @staticmethod
    def generate_osno_xml(
        inn: str,
        period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"],
        year: int,
        income: float,
        expenses: float,
        profit: float,
        loss: float,
        nds: float
    ) -> str:
        """
        Генерация XML для ОСНО (КНД 1151001).
        
        Формат: Декларация по налогу на прибыль организаций
        Версия формата: 5.10
        """
        
        nsmap = {DeclarationXMLGenerator.FNS_PREFIX: DeclarationXMLGenerator.FNS_NAMESPACE}
        root = etree.Element(
            f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Файл",
            nsmap=nsmap
        )
        root.set("ВерсияФормата", "5.10")
        root.set("ИдФайл", f"DECL_OSNO_{inn}_{year}_{period}")
        
        # Титульный лист
        title_page = etree.SubElement(root, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Документ")
        title_page.set("КНД", "1151001")
        title_page.set("НаимДок", "Декларация по налогу на прибыль организаций")
        
        # Сведения о налогоплательщике
        taxpayer = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СвНП")
        inn_elem = etree.SubElement(taxpayer, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}ИННЮЛ")
        inn_elem.text = inn
        
        # Период
        period_elem = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Период")
        period_elem.set("Год", str(year))
        period_elem.set("Код", DeclarationXMLGenerator._get_period_code(period))
        
        # Раздел 1 - Сумма налога к уплате
        section1 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1")
        tax_amount = profit * 0.20  # Ставка налога на прибыль 20%
        tax_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНалУпл")
        tax_elem.text = DeclarationXMLGenerator._format_amount(tax_amount)
        
        # Раздел 2 - Расчет налоговой базы
        section2 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел2")
        
        # Доходы
        income_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Доходы")
        income_elem.text = DeclarationXMLGenerator._format_amount(income)
        
        # Расходы
        expenses_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Расходы")
        expenses_elem.text = DeclarationXMLGenerator._format_amount(expenses)
        
        # Прибыль
        profit_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Прибыль")
        profit_elem.text = DeclarationXMLGenerator._format_amount(profit)
        
        # Убыток
        if loss > 0:
            loss_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Убыток")
            loss_elem.text = DeclarationXMLGenerator._format_amount(loss)
        
        # НДС
        if nds > 0:
            nds_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}НДС")
            nds_elem.text = DeclarationXMLGenerator._format_amount(nds)
        
        # Формирование XML строки
        xml_bytes = etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )
        return xml_bytes.decode("UTF-8")
    
    @staticmethod
    def generate_nds_xml(
        inn: str,
        period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"],
        year: int,
        nds_to_pay: float,
        nds_to_refund: float,
        turnover: float
    ) -> str:
        """
        Генерация XML для НДС (КНД 1151001).
        
        Формат: Декларация по налогу на добавленную стоимость
        Версия формата: 5.10
        """
        
        nsmap = {DeclarationXMLGenerator.FNS_PREFIX: DeclarationXMLGenerator.FNS_NAMESPACE}
        root = etree.Element(
            f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Файл",
            nsmap=nsmap
        )
        root.set("ВерсияФормата", "5.10")
        root.set("ИдФайл", f"DECL_NDS_{inn}_{year}_{period}")
        
        # Титульный лист
        title_page = etree.SubElement(root, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Документ")
        title_page.set("КНД", "1151001")
        title_page.set("НаимДок", "Декларация по налогу на добавленную стоимость")
        
        # Сведения о налогоплательщике
        taxpayer = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СвНП")
        inn_elem = etree.SubElement(taxpayer, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}ИННЮЛ")
        inn_elem.text = inn
        
        # Период
        period_elem = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Период")
        period_elem.set("Год", str(year))
        period_elem.set("Код", DeclarationXMLGenerator._get_period_code(period))
        
        # Раздел 1 - Сумма НДС к уплате/возмещению
        section1 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1")
        
        if nds_to_pay > 0:
            nds_pay_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНДСУпл")
            nds_pay_elem.text = DeclarationXMLGenerator._format_amount(nds_to_pay)
        
        if nds_to_refund > 0:
            nds_refund_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНДСВозм")
            nds_refund_elem.text = DeclarationXMLGenerator._format_amount(nds_to_refund)
        
        # Раздел 2 - Обороты
        section2 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел2")
        turnover_elem = etree.SubElement(section2, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Оборот")
        turnover_elem.text = DeclarationXMLGenerator._format_amount(turnover)
        
        # Формирование XML строки
        xml_bytes = etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )
        return xml_bytes.decode("UTF-8")
    
    @staticmethod
    def generate_6ndfl_xml(
        inn: str,
        period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"],
        year: int,
        total_income: float,
        total_ndfl: float,
        withheld_ndfl: float
    ) -> str:
        """
        Генерация XML для 6-НДФЛ (КНД 1151078).
        
        Формат: Расчет сумм налога на доходы физических лиц
        Версия формата: 5.10
        """
        
        nsmap = {DeclarationXMLGenerator.FNS_PREFIX: DeclarationXMLGenerator.FNS_NAMESPACE}
        root = etree.Element(
            f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Файл",
            nsmap=nsmap
        )
        root.set("ВерсияФормата", "5.10")
        root.set("ИдФайл", f"DECL_6NDFL_{inn}_{year}_{period}")
        
        # Титульный лист
        title_page = etree.SubElement(root, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Документ")
        title_page.set("КНД", "1151078")
        title_page.set("НаимДок", "Расчет сумм налога на доходы физических лиц")
        
        # Сведения о налогоплательщике
        taxpayer = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СвНП")
        inn_elem = etree.SubElement(taxpayer, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}ИННЮЛ")
        inn_elem.text = inn
        
        # Период
        period_elem = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Период")
        period_elem.set("Год", str(year))
        period_elem.set("Код", DeclarationXMLGenerator._get_period_code(period))
        
        # Раздел 1 - Общие показатели
        section1 = etree.SubElement(title_page, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}Раздел1")
        
        total_income_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумДох")
        total_income_elem.text = DeclarationXMLGenerator._format_amount(total_income)
        
        total_ndfl_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНДФЛ")
        total_ndfl_elem.text = DeclarationXMLGenerator._format_amount(total_ndfl)
        
        withheld_ndfl_elem = etree.SubElement(section1, f"{{{DeclarationXMLGenerator.FNS_NAMESPACE}}}СумНДФЛУдерж")
        withheld_ndfl_elem.text = DeclarationXMLGenerator._format_amount(withheld_ndfl)
        
        # Формирование XML строки
        xml_bytes = etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )
        return xml_bytes.decode("UTF-8")
    
    @staticmethod
    def validate_xsd(xml_content: str, xsd_path: str) -> bool:
        """
        Валидация XML по XSD схеме.
        
        Args:
            xml_content: XML строка для валидации
            xsd_path: Путь к XSD схеме
            
        Returns:
            True если XML валиден, False иначе
        """
        
        try:
            if not os.path.exists(xsd_path):
                return False
            
            xml_doc = etree.fromstring(xml_content.encode("UTF-8"))
            xsd_doc = etree.parse(xsd_path)
            xsd_schema = etree.XMLSchema(xsd_doc)
            
            return xsd_schema.validate(xml_doc)
        except Exception:
            return False

