import { api } from "./client";
import type {
  ChatMessage,
  ChatResponse,
  CreateResearchInput,
  DashboardStats,
  InsightReport,
  Page,
  Persona,
  ResearchDetail,
  ResearchSummary,
  SurveyQuestion,
  SurveyResponseItem,
  User,
} from "../types";

export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post<{ access_token: string }>("/auth/register", { email, password, full_name }),
  login: (email: string, password: string) =>
    api.post<{ access_token: string }>("/auth/login", { email, password }),
  me: () => api.get<User>("/auth/me"),
};

export const researchApi = {
  dashboard: () => api.get<DashboardStats>("/research/dashboard"),
  list: (page = 1, pageSize = 10) =>
    api.get<Page<ResearchSummary>>(`/research?page=${page}&page_size=${pageSize}`),
  create: (input: CreateResearchInput) => api.post<ResearchDetail>("/research", input),
  get: (id: string) => api.get<ResearchDetail>(`/research/${id}`),
  remove: (id: string) => api.del<void>(`/research/${id}`),
  personas: (id: string) => api.get<Persona[]>(`/research/${id}/personas`),
  survey: (id: string) => api.get<SurveyQuestion[]>(`/research/${id}/survey`),
  responses: (id: string) => api.get<SurveyResponseItem[]>(`/research/${id}/responses`),
  insights: (id: string) => api.get<InsightReport | null>(`/research/${id}/insights`),
  reportBlob: (id: string) => api.getBlob(`/research/${id}/report`),
};

export const personaApi = {
  chat: (personaId: string, message: string, conversationId?: string) =>
    api.post<ChatResponse>(`/personas/${personaId}/chat`, {
      message,
      conversation_id: conversationId,
    }),
  conversation: (conversationId: string) =>
    api.get<{ id: string; persona_id: string; messages: ChatMessage[] }>(
      `/conversations/${conversationId}`,
    ),
};
