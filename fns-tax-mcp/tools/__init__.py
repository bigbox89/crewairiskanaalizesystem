"""Экспорт всех tools для автоматической регистрации в FastMCP."""
from .generate_usn_declaration import generate_usn_declaration
from .generate_osno_declaration import generate_osno_declaration
from .generate_nds_declaration import generate_nds_declaration
from .generate_6ndfl_declaration import generate_6ndfl_declaration
from .search_companies import search_companies
from .autocomplete import autocomplete
from .get_company_data import get_company_data
from .multinfo_companies import multinfo_companies
from .multcheck_companies import multcheck_companies
from .check_counterparty import check_counterparty
from .check_account_blocks import check_account_blocks, check_account_blocks_file
from .track_changes import track_changes
from .monitor_companies import monitor_companies
from .get_extract import get_extract, get_msp_extract
from .get_accounting_report import get_accounting_report, get_accounting_report_file
from .get_inn_by_passport import get_inn_by_passport
from .check_passport import check_passport, check_passport_info
from .check_person_status import check_person_status
from .get_fsrar_licenses import get_fsrar_licenses
from .get_api_statistics import get_api_statistics

__all__ = [
    "generate_usn_declaration",
    "generate_osno_declaration",
    "generate_nds_declaration",
    "generate_6ndfl_declaration",
    "search_companies",
    "autocomplete",
    "get_company_data",
    "multinfo_companies",
    "multcheck_companies",
    "check_counterparty",
    "check_account_blocks",
    "check_account_blocks_file",
    "track_changes",
    "monitor_companies",
    "get_extract",
    "get_msp_extract",
    "get_accounting_report",
    "get_accounting_report_file",
    "get_inn_by_passport",
    "check_passport",
    "check_passport_info",
    "check_person_status",
    "get_fsrar_licenses",
    "get_api_statistics",
]

