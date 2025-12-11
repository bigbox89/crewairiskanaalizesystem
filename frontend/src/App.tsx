import React, { useEffect, useMemo, useState } from 'react';
import axios, { AxiosError } from 'axios';
import { pdfjs } from 'react-pdf';
import ChatMessage from './components/ChatMessage';
import { parseAgentResponse } from './lib/parser';
import { ApiSendResponse, ChatEntry } from './types';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.js',
  import.meta.url,
).toString();

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8010/api/send';

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState('');
  const [token, setToken] = useState<string>(() => localStorage.getItem('agent_token') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [missingPrompt, setMissingPrompt] = useState<string[]>([]);
  const [missingInput, setMissingInput] = useState('');
  const [debug, setDebug] = useState(false);

  useEffect(() => {
    localStorage.setItem('agent_token', token);
  }, [token]);

  const submitMessage = async (messageText: string) => {
    if (!messageText.trim()) return;
    setError(null);
    const timestamp = new Date().toLocaleString();
    const userEntry: ChatEntry = {
      id: crypto.randomUUID(),
      role: 'user',
      timestamp,
      parsed: {
        displayText: messageText,
        riskBadges: [],
        tables: [],
        files: [],
        missingData: [],
      },
    };
    setMessages((prev) => [...prev, userEntry]);

    setLoading(true);
    const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

    const performRequest = async () => {
      const res = await axios.post<ApiSendResponse>(
        API_URL,
        { message: messageText },
        { headers },
      );
      return res.data;
    };

    let responseData: ApiSendResponse | null = null;
    try {
      responseData = await performRequest();
    } catch (err) {
      const axiosErr = err as AxiosError;
      const status = axiosErr.response?.status;
      if (status && status >= 500) {
        // retry once on server errors
        try {
          responseData = await performRequest();
        } catch (retryErr) {
          setError(
            `Ошибка сервера (${status}). Повторите запрос позже. Детали: ${
              (retryErr as AxiosError).message
            }`,
          );
        }
      } else {
        setError(
          `Ошибка запроса${status ? ` (${status})` : ''}: ${
            axiosErr.message || 'неизвестно'
          }`,
        );
      }
    } finally {
      setLoading(false);
    }

    if (!responseData) return;

    if (responseData.ok === false) {
      setError(responseData.detail || responseData.error || 'Неизвестная ошибка');
    }

    const parsed = parseAgentResponse(responseData.data ?? responseData);
    const agentEntry: ChatEntry = {
      id: crypto.randomUUID(),
      role: 'agent',
      timestamp: new Date().toLocaleString(),
      parsed,
      error: responseData.ok === false ? responseData.detail || responseData.error : undefined,
    };
    setMessages((prev) => [...prev, agentEntry]);

    if (parsed.missingData.length) {
      setMissingPrompt(parsed.missingData);
    }
  };

  const handleSend = async () => {
    await submitMessage(input);
    setInput('');
  };

  const handleMissingSubmit = async () => {
    if (!missingInput.trim()) {
      setMissingPrompt([]);
      return;
    }
    await submitMessage(`Дополнительные данные: ${missingInput}`);
    setMissingInput('');
    setMissingPrompt([]);
  };

  const headerInfo = useMemo(
    () => ({
      title: 'Риск-оценка (A2A агент)',
      subtitle: 'Подключение к /api/send. Тёмная тема, чат как Telegram.',
    }),
    [],
  );

  return (
    <div className="flex min-h-screen flex-col bg-neutral-900 text-gray-100">
      <header className="border-b border-neutral-800 bg-neutral-950/60 px-4 py-3 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">{headerInfo.title}</h1>
            <p className="text-sm text-gray-400">{headerInfo.subtitle}</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              className="w-56 rounded-lg bg-neutral-800 px-3 py-2 text-xs text-gray-100 outline-none ring-1 ring-neutral-700 focus:ring-blue-500"
              placeholder="Bearer token (опционально)"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <span className="text-xs text-gray-500">auth header</span>
            <button
              className="rounded-lg bg-neutral-800 px-3 py-2 text-xs text-gray-100 ring-1 ring-neutral-700 hover:ring-blue-500"
              onClick={() => setDebug((v) => !v)}
            >
              {debug ? 'Debug: ON' : 'Debug: OFF'}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-5xl flex-col gap-4">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-800 p-4 text-sm text-gray-300">
              Введите запрос, например: <br />
              <span className="text-white">
                «дай комплексную оценку риска по ИНН 9717025654»
              </span>
            </div>
          )}
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} debug={debug} />
          ))}
        </div>
      </main>

      <footer className="sticky bottom-0 border-t border-neutral-800 bg-neutral-950/80 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-col gap-3">
          {error && (
            <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
            <textarea
              className="min-h-[72px] flex-1 rounded-xl bg-neutral-900 px-3 py-3 text-sm text-gray-100 outline-none ring-1 ring-neutral-700 focus:ring-blue-500"
              placeholder="Напишите сообщение..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              className="h-[48px] rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow hover:bg-blue-500 disabled:opacity-60"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              {loading ? 'Отправка...' : 'Отправить'}
            </button>
          </div>
        </div>
      </footer>

      {missingPrompt.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-lg rounded-2xl border border-neutral-700 bg-neutral-900 p-5 shadow-2xl">
            <h3 className="text-lg font-semibold text-white">Нужны уточнения</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-200">
              {missingPrompt.map((m, idx) => (
                <li key={idx}>{m}</li>
              ))}
            </ul>
            <textarea
              className="mt-3 w-full rounded-lg bg-neutral-800 px-3 py-2 text-sm text-gray-100 outline-none ring-1 ring-neutral-700 focus:ring-blue-500"
              placeholder="Введите уточняющие данные..."
              value={missingInput}
              onChange={(e) => setMissingInput(e.target.value)}
            />
            <div className="mt-3 flex justify-end gap-2">
              <button
                className="rounded-lg px-3 py-2 text-sm text-gray-200 ring-1 ring-neutral-700"
                onClick={() => {
                  setMissingPrompt([]);
                  setMissingInput('');
                }}
              >
                Отмена
              </button>
              <button
                className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white"
                onClick={handleMissingSubmit}
              >
                Отправить уточнение
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;

