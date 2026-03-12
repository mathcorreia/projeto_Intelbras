import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { CameraDetailComponent } from './pages/camera-detail/camera-detail.component';
import { CameraAddComponent } from './pages/camera-add/camera-add.component'; 
import { LogsComponent } from './pages/logs/logs.component';
import { SecurityHubComponent } from './pages/hub-modules/security-hub.component';
import { HomeHubComponent } from './pages/home-hub/home-hub.component';
import { AccessManagementComponent } from './pages/access-management/access-management.component';
import { GateManagementComponent } from './pages/gate-management/gate-management.component'; 
import { AlarmManagementComponent } from './pages/alarm-management/alarm-management.component';

export const routes: Routes = [
    // 1. A Raiz (Home) abre o Hub Principal
    { path: '', component: HomeHubComponent },

    // 2. O Monitoramento de Câmaras fica em '/dashboard'
    { path: 'dashboard', component: DashboardComponent },

    // 3. A página de integrações (Portões/Alarmes) fica em '/hub'
    { path: 'hub', component: SecurityHubComponent },

    // Detalhes da câmara
    { path: 'camera/:id', component: CameraDetailComponent },

    // Adicionar e Editar
    { path: 'camera-add', component: CameraAddComponent },
    { path: 'camera-edit/:id', component: CameraAddComponent },
     
    { path: 'logs', component: LogsComponent },

    { path: 'gestao-acessos', component: AccessManagementComponent },
    { path: 'gestao-portoes', component: GateManagementComponent },
    { path: 'gestao-alarmes', component: AlarmManagementComponent },

    { path: '**', redirectTo: '' },
];