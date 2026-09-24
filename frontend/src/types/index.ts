export type ResearchStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface ResearchSummary {
  id: string;
  title: string;
  status: ResearchStatus;
  num_personas: number;
  num_questions: number;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface ResearchDetail extends ResearchSummary {
  product_description: string;
  target_audience: string;
  research_goal: string;
  model_used: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface DashboardStats {
  total: number;
  completed: number;
  running: number;
  failed: number;
  pending: number;
  recent: ResearchSummary[];
}

export interface Persona {
  id: string;
  slug: string;
  name: string;
  age: number;
  occupation: string;
  background: string;
  personality_traits: string[];
  behavioral_patterns: string[];
  psychological_profile: string;
  goals: string[];
  pain_points: string[];
  tech_savviness: string;
  communication_style: string;
  persona_summary: string;
}

export interface SurveyQuestion {
  id: string;
  slug: string;
  order_index: number;
  text: string;
  question_type: string;
  options: string[] | null;
  rationale: string;
}

export interface SurveyResponseItem {
  id: string;
  question_id: string;
  persona_slug: string;
  answer: string;
  sentiment: string;
  confidence: number;
}

export interface Theme {
  id: string;
  title: string;
  description: string;
  prevalence: string;
  supporting_persona_ids: string[];
}

export interface InsightReport {
  id: string;
  executive_summary: string;
  overall_sentiment: string;
  notable_quotes: string[];
  weak_areas_or_risks: string[];
  recommendations: string[];
  themes: Theme[];
  disclaimer: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "persona";
  content: string;
  order_index: number;
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  reply: ChatMessage;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateResearchInput {
  title: string;
  product_description: string;
  target_audience: string;
  research_goal: string;
  num_personas: number;
  num_questions: number;
}
