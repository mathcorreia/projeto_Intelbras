import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router'; // <-- Make sure this is imported

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet], // <-- Make sure RouterOutlet is here
  template: '<router-outlet></router-outlet>', // <-- This should be the ONLY thing in the template
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  // This component's logic can be empty
}