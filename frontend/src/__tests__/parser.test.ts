import { parseAgentResponse } from '../lib/parser';

describe('parseAgentResponse', () => {
  it('parses structured reasoning block', () => {
    const raw = {
      reasoning: 'Компания банкрот с долгами.',
      tools: ['get_company_data'],
      missing_data: ['данные о блокировках счетов'],
      confidence: 'высокий',
    };
    const parsed = parseAgentResponse(raw);

    expect(parsed.displayText).toContain('Резюме');
    expect(parsed.displayText).toContain('Компания банкрот');
    expect(parsed.missingData).toContain('данные о блокировках счетов');
  });

  it('extracts risk percentages for chart', () => {
    const raw = {
      formatted: 'ФНС 40%, Арбитраж 50%, Банк 10%',
    };
    const parsed = parseAgentResponse(raw);
    expect(parsed.riskChart?.values).toEqual([40, 50, 10]);
  });

  it('finds files and tables', () => {
    const raw = {
      text: 'Скачайте выписку: http://example.com/report.pdf',
      data: {
        deals: [
          { id: 1, status: 'open' },
          { id: 2, status: 'closed' },
        ],
      },
    };
    const parsed = parseAgentResponse(raw);
    expect(parsed.files[0].url).toContain('report.pdf');
    expect(parsed.tables[0].columns).toEqual(expect.arrayContaining(['id', 'status']));
  });
});

