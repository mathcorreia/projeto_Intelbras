package com.intelbrasKoreon.intelbrasKoreon.user;

import com.intelbrasKoreon.intelbrasKoreon.tenant.Tenant;
import com.intelbrasKoreon.intelbrasKoreon.tenant.TenantService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final TenantService tenantService;
    private final PasswordEncoder passwordEncoder;

    public List<User> findByTenant(Long tenantId) {
        return userRepository.findAllByTenantId(tenantId);
    }

    public User findById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Usuário não encontrado: " + id));
    }

    public User create(Long tenantId, String name, String email, String password, UserRole role) {
        if (userRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("E-mail já cadastrado: " + email);
        }
        Tenant tenant = tenantService.findById(tenantId);
        User user = User.builder()
                .tenant(tenant)
                .name(name)
                .email(email)
                .passwordHash(passwordEncoder.encode(password))
                .role(role)
                .build();
        return userRepository.save(user);
    }

    public User setActive(Long id, boolean active) {
        User user = findById(id);
        user.setActive(active);
        return userRepository.save(user);
    }

    public User changeRole(Long id, UserRole role) {
        User user = findById(id);
        user.setRole(role);
        return userRepository.save(user);
    }

    public User resetPassword(Long id, String newPassword) {
        User user = findById(id);
        user.setPasswordHash(passwordEncoder.encode(newPassword));
        return userRepository.save(user);
    }
}
