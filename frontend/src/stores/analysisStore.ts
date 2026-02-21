import { create } from 'zustand';
import type { AnalysisResult, HistoryRecord } from '../types/analysis';
import { runAnalysis, getHistory, getHistoryDetail } from '../api/client';

interface AnalysisState {
  result: AnalysisResult | null;
  loading: boolean;
  error: string | null;
  activeTab: 'fundamental' | 'technical' | 'sentiment';
  history: HistoryRecord[];
  historyLoading: boolean;
  aiProvider: string;

  analyze: (code: string) => Promise<void>;
  setActiveTab: (tab: 'fundamental' | 'technical' | 'sentiment') => void;
  setAiProvider: (provider: string) => void;
  fetchHistory: () => Promise<void>;
  loadHistoryDetail: (id: number) => Promise<void>;
  clearResult: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  result: null,
  loading: false,
  error: null,
  activeTab: 'fundamental',
  history: [],
  historyLoading: false,
  aiProvider: 'gemini',

  analyze: async (code: string) => {
    set({ loading: true, error: null, result: null });
    try {
      const result = await runAnalysis({ code, ai_provider: get().aiProvider });
      set({ result, loading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || err.message || 'Analysis failed',
        loading: false,
      });
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  setAiProvider: (provider) => set({ aiProvider: provider }),

  fetchHistory: async () => {
    set({ historyLoading: true });
    try {
      const history = await getHistory();
      set({ history, historyLoading: false });
    } catch {
      set({ historyLoading: false });
    }
  },

  loadHistoryDetail: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const result = await getHistoryDetail(id);
      set({ result: result as AnalysisResult, loading: false });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  clearResult: () => set({ result: null, error: null }),
}));
