import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ChatMessage, ChatResponse, ForecastResponse, StrategyResponse } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private readonly http: HttpClient) {}

  private getCurrentLocalDateIso(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  runStrategy(query: string, sessionId: string, anchorDate = this.getCurrentLocalDateIso()): Observable<StrategyResponse> {
    return this.http.post<StrategyResponse>(`${this.baseUrl}/strategy`, {
      query,
      session_id: sessionId,
      anchor_date: anchorDate,
    });
  }

  getForecast(anchorDate = this.getCurrentLocalDateIso()): Observable<ForecastResponse> {
    return this.http.post<ForecastResponse>(`${this.baseUrl}/forecast`, {
      anchor_date: anchorDate,
    });
  }

  sendChat(question: string, sessionId: string, history: ChatMessage[]): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, {
      question,
      session_id: sessionId,
      history,
    });
  }
}
