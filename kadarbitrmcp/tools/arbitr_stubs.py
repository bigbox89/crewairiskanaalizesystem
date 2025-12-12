"""Stub data for test mode."""

import base64


def stub_search_cases() -> dict:
    return {
        "Success": 1,
        "Cases": [
            {
                "CaseId": "7057cbe9-910b-43ab-98f6-97293fbfd6ff",
                "CaseNumber": "А40-180791/2024",
                "CaseType": "Б",
                "Court": "АС города Москвы",
                "StartDate": "2024-08-05",
                "Plaintiffs": [
                    {
                        "Name": "ПАО \"НОРВИК БАНК\"",
                        "Address": "115054, Россия, г Москва, г. Москва, ул. Зацепский вал, д. 5",
                        "Inn": "4346001485",
                    }
                ],
                "Respondents": [
                    {"Name": "Антоненко Александр Александрович", "Address": None, "Inn": "463406307502"}
                ],
            }
        ],
        "PagesCount": 1,
    }


def stub_details_by_number() -> dict:
    return {
        "Success": 1,
        "Cases": [
            {
                "CaseId": "6fb9afec-b71d-4183-b917-4cace5958c16",
                "CaseNumber": "А71-1202/2015",
                "CaseType": "А",
                "Plaintiffs": [
                    {
                        "Name": "ООО \"Детство\"",
                        "Address": "101000, ул. Петровка 17/3-19 (Мансурову М.С.), Москва г.",
                        "Inn": "1841012052",
                        "Ogrn": "1101841004198",
                        "Id": "3c79f2f9-c07f-4cfe-92a1-eb495e3fd2de",
                    }
                ],
                "Respondents": [
                    {
                        "Name": "Межрайонная ИФНС России №9 по Удмуртской Республике",
                        "Address": "426003, ул. Карла Маркса, 130, г. Ижевск",
                        "Inn": "1835059990",
                        "Ogrn": "1041805001501",
                        "Id": "b49d872b-2fd3-4802-904d-8c8565ad6fea",
                    }
                ],
                "StartDate": "2015-02-06",
                "State": "Рассмотрение дела завершено",
                "Finished": True,
                "CaseInstances": [
                    {
                        "Id": "5400123c-5c8a-4421-a839-c130938086c2",
                        "InstanceNumber": "А71-1202/15",
                        "Name": "Первая инстанция",
                        "State": "Следующее заседание: 18.11.2020, 10:15 , №217 Матвеева Н.В.",
                        "Court": {"Code": "UDMURTIYA", "Name": "АС Удмуртской Республики"},
                        "File": {
                            "Name": "A71-1202-2015_20150507_Reshenija i postanovlenija.pdf",
                            "URL": "https://kad.arbitr.ru/PdfDocument/63778dcd-c696-4863-b781-73a839cbf8a8/A71-1202-2015_20150507_Reshenija%20i%20postanovlenija.pdf",
                        },
                        "Judges": ["Бушуева Е. А."],
                        "MoiArbitrDocuments": [
                            {
                                "PublishDate": "2016-11-21 10:25:00",
                                "RegisterDate": "2016-11-21",
                                "DocumentName": "Отзыв",
                                "CourtName": "АС Удмуртской Республики",
                            }
                        ],
                        "InstanceEvents": [
                            {
                                "EventTypeName": "Определение",
                                "EventTypeId": "3f4a11f5-b269-4fe8-8243-957b5260c3d1",
                                "Id": "8d0e1fc6-9df7-46bb-8530-10a971190666",
                                "AdditionalInfo": "Дата и время судебного заседания 20.01.2016, 11:00, 22",
                                "Date": "2015-12-11",
                                "File": "https://kad.arbitr.ru/PdfDocument/8d0e1fc6-9df7-46bb-8530-10a971190666/A71-1202-2015_20151211_Opredelenie.pdf",
                                "PublishDate": "2015-12-12",
                                "FinishEvent": 0,
                                "EventContentTypeName": "Об отложении рассмотрения заявления/жалобы",
                                "Declarer": "АНО ДАЧНОЕ НЕКОММЕРЧЕСКОЕ ТОВАРИЩЕСТВО ВНИИКОП-ОСТРОВ",
                                "DeclarerInn": "5003079985",
                                "Comment": "заявителю на руки в заседании, ответчику на руки в ячейке",
                                "DecisionTypeName": None,
                                "HasSignature": 0,
                                "ClaimSum": 10000,
                            }
                        ],
                    }
                ],
                "CourtHearings": [
                    {
                        "Location": "426011, Ижевск, ул. Ломоносова 5, 22",
                        "Summary": "Заседание по делу А71-1202/2015 в АС Удмуртской Республики. Судья Бушуева Е. А.",
                        "Start": "2015-03-19T11:00:00+04",
                        "End": "2015-03-19T12:00:00+04",
                    }
                ],
            }
        ],
    }


def stub_details_by_id() -> dict:
    return stub_details_by_number()


def stub_pdf_download() -> dict:
    minimal_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\n"
        b"endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n"
        b"<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n"
        b"178\n"
        b"%%EOF"
    )
    return {"Success": 1, "pdfContent": base64.b64encode(minimal_pdf).decode("utf-8")}


