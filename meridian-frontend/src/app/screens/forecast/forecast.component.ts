import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { ApiService } from '../../shared/api.service';
import { ForecastPoint, ForecastRisk } from '../../shared/models';

@Component({
  selector: 'app-forecast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './forecast.component.html',
  styleUrl: './forecast.component.css',
})
export class ForecastComponent {
  loading = false;
  error = '';
  model = '';
  points: ForecastPoint[] = [];
  risks: ForecastRisk[] = [];

  constructor(private readonly api: ApiService) {}

  loadForecast(): void {
    this.loading = true;
    this.error = '';
    this.api.getForecast().subscribe({
      next: (result) => {
        this.model = result.model;
        this.points = result.forecast_by_day_category;
        this.risks = result.stockout_risks.slice(0, 25);
        this.loading = false;
      },
      error: () => {
        this.error = 'Unable to load forecast data from Lambda.';
        this.loading = false;
      },
    });
  }
}