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
import { GuaritaComponent } from './pages/guarita/guarita.component';
import { LoginComponent } from './pages/login/login.component';

export const routes: Routes = [
    { path: 'login', component: LoginComponent },

    { path: '', component: HomeHubComponent },
    { path: 'dashboard', component: DashboardComponent },
    { path: 'hub', component: SecurityHubComponent },

    { path: 'camera/:id', component: CameraDetailComponent },
    { path: 'camera-add', component: CameraAddComponent },
    { path: 'camera-edit/:id', component: CameraAddComponent },

    { path: 'logs', component: LogsComponent },
    { path: 'gestao-acessos', component: AccessManagementComponent },
    { path: 'gestao-portoes', component: GateManagementComponent },
    { path: 'gestao-alarmes', component: AlarmManagementComponent },
    { path: 'guarita', component: GuaritaComponent },

    { path: '**', redirectTo: '' },
];
