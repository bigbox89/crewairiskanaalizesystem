import asyncio
from config import reload_settings
from tools.arbitr_client import ArbitrApiClient, ArbitrApiError

async def main():
    settings = reload_settings()
    client = ArbitrApiClient(settings)

    search = await client.search_cases(Inn="ROSNEFT", DateFrom="2020-10-16", DateTo="2020-11-16")
    print("search_cases Success", search.get("Success"), "count", len(search.get("Cases", [])))

    cases = search.get("Cases", [])
    case_id = cases[0].get("CaseId") if cases else "b82051d4-9713-4dcd-8de5-ef6d18d8ac66"

    details_num = await client.details_by_number("A71-1202/2015")
    print("details_by_number Success", details_num.get("Success"), "cases", len(details_num.get("Cases", [])))

    details_id = await client.details_by_id(case_id)
    print("details_by_id Success", details_id.get("Success"), "cases", len(details_id.get("Cases", [])), "case_id", case_id)

    pdf = await client.download_pdf("https://kad.arbitr.ru/PdfDocument/63778dcd-c696-4863-b781-73a839cbf8a8/A71-1202-2015_20150507_Reshenija%20i%20postanovlenija.pdf")
    print("pdf Success", pdf.get("Success"), "has_pdf", bool(pdf.get("pdfContent")))

try:
    asyncio.run(main())
except ArbitrApiError as e:
    print("API error", e.status_code, e.error_code, str(e))
