import React, { useMemo, useState } from 'react';
import classNames from 'classnames';
import ReactMarkdown from 'react-markdown';
import { Document, Page } from 'react-pdf';
import DataTable from './DataTable';
import RiskChart from './RiskChart';
import { ChatEntry, ParsedTable } from '../types';

interface ChatMessageProps {
  message: ChatEntry;
  debug?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, debug = false }) => {
  const isUser = message.role === 'user';
  const [showDetails, setShowDetails] = useState(false);

  const [userTables, debugTables] = useMemo(() => {
    const tables = message.parsed.tables || [];
    const userT: ParsedTable[] = [];
    const dbgT: ParsedTable[] = [];
    tables.forEach((t) => {
      const title = (t.title || '').toLowerCase();
      if (title.includes('artifact') || title.includes('history')) {
        dbgT.push(t);
      } else {
        userT.push(t);
      }
    });
    return [userT, dbgT];
  }, [message.parsed.tables]);

  return (
    <div className={classNames('flex w-full gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="mt-2 h-8 w-8 rounded-full bg-blue-600 text-center text-sm font-semibold text-white">
          AI
        </div>
      )}
      <div
        className={classNames(
          'max-w-3xl rounded-2xl px-4 py-3 shadow',
          isUser ? 'bg-bubble-gray text-gray-100' : 'bg-bubble-blue text-white',
        )}
      >
        <div className="mb-1 text-xs text-gray-200 opacity-70">{message.timestamp}</div>
        {message.error ? (
          <p className="text-sm text-red-200">{message.error}</p>
        ) : (
          <>
            <RichText text={message.parsed.displayText} />
            <Badges badges={message.parsed.riskBadges} />
            {message.parsed.showPieChart && message.parsed.riskChart && (
              <div className="mt-3 rounded-lg border border-neutral-700 bg-neutral-900 p-3">
                <RiskChart data={message.parsed.riskChart} />
              </div>
            )}
            {(message.parsed.showTable || debug) && userTables.length > 0 && (
              <div className="mt-3 space-y-2">
                {userTables.map((t, idx) => (
                  <DataTable table={t} key={`${message.id}-table-${idx}`} />
                ))}
              </div>
            )}
            {message.parsed.files.length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-semibold">Файлы / выписки</p>
                {message.parsed.files.map((file, idx) => (
                  <div
                    key={`${file.url}-${idx}`}
                    className="rounded-lg border border-neutral-700 bg-neutral-900 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <a
                        href={file.url}
                        target="_blank"
                        className="text-blue-200 underline"
                        rel="noreferrer"
                      >
                        Скачать ({file.label || 'файл'})
                      </a>
                      <span className="text-xs text-gray-400 break-all">{file.url}</span>
                    </div>
                    {file.url.toLowerCase().endsWith('.pdf') && (
                      <div className="mt-2 overflow-hidden rounded border border-neutral-800 bg-black/30">
                        <Document file={file.url}>
                          <Page pageNumber={1} width={360} />
                        </Document>
                        <p className="px-3 py-1 text-xs text-gray-400">Превью первой страницы</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            {message.parsed.missingData.length > 0 && (
              <div className="mt-3 rounded-lg border border-yellow-400/40 bg-yellow-500/10 p-3 text-sm text-yellow-100">
                Требуются уточнения:
                <ul className="ml-4 list-disc">
                  {message.parsed.missingData.map((m, idx) => (
                    <li key={`${message.id}-miss-${idx}`}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
            {(debugTables.length > 0 || message.parsed.raw) && (
              <div className="mt-3">
                <button
                  className="rounded bg-neutral-800 px-3 py-1 text-xs text-gray-200 ring-1 ring-neutral-700 hover:ring-blue-500"
                  onClick={() => setShowDetails((v) => !v)}
                >
                  {showDetails ? 'Скрыть детали' : 'Показать детали'}
                </button>
                {showDetails && (
                  <div className="mt-2 space-y-2">
                    {debugTables.map((t, idx) => (
                      <DataTable table={t} key={`${message.id}-dbgtable-${idx}`} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
      {isUser && (
        <div className="mt-2 h-8 w-8 rounded-full bg-neutral-700 text-center text-sm font-semibold text-white">
          U
        </div>
      )}
    </div>
  );
};

const RichText: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  return (
    <div className="prose prose-invert prose-sm max-w-none">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
};

const Badges: React.FC<{ badges: ChatEntry['parsed']['riskBadges'] }> = ({ badges }) => {
  if (!badges.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {badges.map((b, idx) => (
        <span
          key={`${b.label}-${idx}`}
          className={classNames(
            'rounded-full px-3 py-1 text-xs font-semibold',
            b.colorClass,
          )}
        >
          {b.emoji} {b.label}
        </span>
      ))}
    </div>
  );
};

export default ChatMessage;

