import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../shared/api.service';
import { ChatMessage } from '../../shared/models';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent {
  sessionId = `chat-${Date.now()}`;
  loading = false;
  prompt = 'How should I plan stock for milk carton SKUs with active promotions?';
  messages: ChatMessage[] = [];
  error = '';
  suggestedQuestions: string[] = [
    'How much milk should I stock for next 10 days?',
    'Which SKUs have highest stockout risk this week?',
    'What should I reorder first for promoted carton packs?',
    'Show quick reorder plan by region for beverages.',
    'Which categories need price increase due to mandi/weather signals?',
  ];

  constructor(private readonly api: ApiService) {}

  applySuggestion(value: string): void {
    if (!value) {
      return;
    }
    this.prompt = value;
  }

  ask(): void {
    if (!this.prompt.trim()) {
      return;
    }

    const question = this.prompt.trim();
    this.messages = [...this.messages, { role: 'user', content: question }];
    this.prompt = '';
    this.loading = true;
    this.error = '';

    this.api.sendChat(question, this.sessionId, this.messages).subscribe({
      next: (result) => {
        const content = result.error ? `Error: ${result.error}` : result.answer;
        this.messages = [...this.messages, { role: 'assistant', content }];
        this.loading = false;
      },
      error: () => {
        this.error = 'Unable to reach chat Lambda endpoint.';
        this.loading = false;
      },
    });
  }

  formatMessage(content: string): string {
    const escaped = content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    return escaped
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^###\s+(.*)$/gm, '<strong>$1</strong>')
      .replace(/^- (.*)$/gm, '• $1')
      .replace(/\n/g, '<br/>');
  }
}
