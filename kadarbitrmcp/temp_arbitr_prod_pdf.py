import asyncio
from config import reload_settings
from tools.arbitr_client import ArbitrApiClient, ArbitrApiError

async def main():
    settings = reload_settings()
    client = ArbitrApiClient(settings)
    try:
        pdf = await client.download_pdf("https://kad.arbitr.ru/PdfDocument/63778dcd-c696-4863-b781-73a839cbf8a8/A71-1202-2015_20150507_Reshenija%20i%20postanovlenija.pdf")
        print("pdf raw:", pdf)
    except ArbitrApiError as e:
        print("API error", e.status_code, e.error_code, str(e))

asyncio.run(main())
