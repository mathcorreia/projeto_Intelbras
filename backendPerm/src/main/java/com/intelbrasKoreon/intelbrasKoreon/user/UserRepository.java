package com.intelbrasKoreon.intelbrasKoreon.user;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findAllByTenantId(Long tenantId);
    boolean existsByEmail(String email);
}
