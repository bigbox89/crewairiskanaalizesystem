export type Role = 'user' | 'agent';

export interface ParsedTable {
  title?: string;
  columns: string[];
  rows: Record<string, any>[];
}

export interface ParsedFile {
  url: string;
  label?: string;
  mime?: string;
}

export interface RiskBadge {
  label: string;
  emoji?: string;
  level: 'high' | 'medium' | 'low';
  colorClass: string;
}

export interface RiskChartData {
  labels: string[];
  values: number[];
  colors: string[];
}

export interface ParsedMessage {
  displayText: string;
  riskBadges: RiskBadge[];
  riskChart?: RiskChartData;
  showPieChart?: boolean;
  showTable?: boolean;
  artifacts?: any;
  history?: any;
  tables: ParsedTable[];
  files: ParsedFile[];
  missingData: string[];
  raw?: any;
}

export interface ChatEntry {
  id: string;
  role: Role;
  timestamp: string;
  parsed: ParsedMessage;
  error?: string;
}

export interface ApiSendResponse {
  ok?: boolean;
  data?: any;
  detail?: string;
  error?: string;
  [key: string]: any;
}

