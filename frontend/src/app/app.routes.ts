import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { CameraDetailComponent } from './pages/camera-detail/camera-detail.component';
import { CameraAddComponent } from './pages/camera-add/camera-add.component'; // <-- Adicione esta importação

export const routes: Routes = [
    // Rota principal, mostra a lista de câmaras
    { path: 'dashboard', component: DashboardComponent },

    // Rota para ver os detalhes de UMA câmara. O ':id' é um parâmetro dinâmico.
    { path: 'camera/:id', component: CameraDetailComponent },

    // Rota para adicionar uma nova câmara
     { path: 'camera-add', component: CameraAddComponent },

    // Se o utilizador aceder à raiz, redireciona para o dashboard
    { path: '', redirectTo: '/dashboard', pathMatch: 'full' },

    // Se o URL não corresponder a nada, redireciona para o dashboard
    { path: '**', redirectTo: '/dashboard' }
];