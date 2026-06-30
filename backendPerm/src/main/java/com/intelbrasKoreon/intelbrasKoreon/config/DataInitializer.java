package com.intelbrasKoreon.intelbrasKoreon.config;

import com.intelbrasKoreon.intelbrasKoreon.tenant.Tenant;
import com.intelbrasKoreon.intelbrasKoreon.tenant.TenantRepository;
import com.intelbrasKoreon.intelbrasKoreon.user.User;
import com.intelbrasKoreon.intelbrasKoreon.user.UserRepository;
import com.intelbrasKoreon.intelbrasKoreon.user.UserRole;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Order(1)
@RequiredArgsConstructor
public class DataInitializer implements ApplicationRunner {

    private final TenantRepository tenantRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${ADMIN_EMAIL:admin@koreontech.com}")
    private String adminEmail;

    @Value("${ADMIN_PASSWORD:admin123}")
    private String adminPassword;

    @Override
    public void run(ApplicationArguments args) {
        if (tenantRepository.count() > 0) return;

        log.info("[DataInitializer] Criando tenant e super-admin padrão...");

        Tenant tenant = tenantRepository.save(
                Tenant.builder()
                        .name("Koreon Tech")
                        .slug("koreontech")
                        .plan("enterprise")
                        .build()
        );

        userRepository.save(
                User.builder()
                        .tenant(tenant)
                        .name("Super Admin")
                        .email(adminEmail)
                        .passwordHash(passwordEncoder.encode(adminPassword))
                        .role(UserRole.SUPER_ADMIN)
                        .build()
        );

        log.info("[DataInitializer] Super-admin criado: {} / {}", adminEmail, adminPassword);
        log.warn("[DataInitializer] MUDE a senha do admin em produção! Use env ADMIN_PASSWORD.");
    }
}
