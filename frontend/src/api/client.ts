import axios from 'axios';
import type { AnalysisRequest, AnalysisResult, HistoryRecord } from '../types/analysis';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || '') + '/api/v1',
  timeout: 300000, // 5 min for full analysis
});

export async function runAnalysis(req: AnalysisRequest): Promise<AnalysisResult> {
  const { data } = await api.post('/analyze', req);
  return data;
}

export async function getStockInfo(code: string) {
  const { data } = await api.get(`/stocks/${code}/info`);
  return data;
}

export async function getStockDaily(code: string, days = 365) {
  const { data } = await api.get(`/stocks/${code}/daily`, { params: { days } });
  return data;
}

export async function getStockFinancials(code: string) {
  const { data } = await api.get(`/stocks/${code}/financials`);
  return data;
}

export async function getHistory(limit = 50): Promise<HistoryRecord[]> {
  const { data } = await api.get('/history', { params: { limit } });
  return data;
}

export async function getHistoryDetail(id: number): Promise<AnalysisResult> {
  const { data } = await api.get(`/history/${id}`);
  return data;
}
