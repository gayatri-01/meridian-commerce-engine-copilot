import { Routes } from '@angular/router';

import { LandingComponent } from './screens/landing/landing.component';
import { HomeComponent } from './screens/home/home.component';
import { ForecastComponent } from './screens/forecast/forecast.component';
import { ChatComponent } from './screens/chat/chat.component';

export const appRoutes: Routes = [
  { path: '', component: LandingComponent },
  { path: 'strategy', component: HomeComponent },
  { path: 'forecast', component: ForecastComponent },
  { path: 'chat', component: ChatComponent },
  { path: '**', redirectTo: '' },
];
