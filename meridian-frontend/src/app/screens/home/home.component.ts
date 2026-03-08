import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { ApiService } from '../../shared/api.service';
import { StrategyCard, StrategyStep } from '../../shared/models';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent {
  query = 'Provide a retail opportunity report for the next 15 days in Dombivli.';
  sessionId = `strategy-${Date.now()}`;
  anchorDate = this.getCurrentLocalDateIso();
  loading = false;
  error = '';

  steps: StrategyStep[] = [];
  renderedSteps: StrategyStep[] = [];
  cards: StrategyCard[] = [];

  constructor(private readonly api: ApiService) {}

  private getCurrentLocalDateIso(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  refresh(): void {
    this.loading = true;
    this.error = '';
    this.steps = [];
    this.renderedSteps = [];
    this.cards = [];

    this.anchorDate = this.getCurrentLocalDateIso();
    this.api.runStrategy(this.query, this.sessionId, this.anchorDate).subscribe({
      next: (result) => {
        this.anchorDate = result.anchor_date || this.anchorDate;
        this.steps = result.steps || [];
        this.replaySteps(this.steps, () => {
          this.cards = result.cards || [];
          this.loading = false;
        });
      },
      error: () => {
        this.error = 'Unable to fetch strategy report from Lambda.';
        this.loading = false;
      },
    });
  }

  private replaySteps(steps: StrategyStep[], done: () => void): void {
    if (!steps.length) {
      done();
      return;
    }

    steps.forEach((step, index) => {
      setTimeout(() => {
        this.renderedSteps = [...this.renderedSteps, step];
        if (index === steps.length - 1) {
          setTimeout(done, 500);
        }
      }, 550 * (index + 1));
    });
  }
}
