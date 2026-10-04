package com.intelbrasKoreon.intelbrasKoreon.user;

public enum UserRole {
    SUPER_ADMIN,   // Koreon Tech internal — acessa todos os tenants
    TENANT_ADMIN,  // Administrador do tenant
    OPERATOR,      // Operador de segurança
    GUARD,         // Operador de guarita
    VIEWER         // Somente leitura
}
