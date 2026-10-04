import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-home-hub',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './home-hub.component.html',
  styleUrls: ['./home-hub.component.scss']
})
export class HomeHubComponent implements OnDestroy {
  
  systemStatus = {
    camerasOnline: 64, // Exemplo
    doorsLocked: 12,   // Exemplo
  };

  currentTime = new Date();
  private timer: any;

  constructor() {
    
    this.timer = setInterval(() => {
      this.currentTime = new Date();
    }, 1000);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
  }
}