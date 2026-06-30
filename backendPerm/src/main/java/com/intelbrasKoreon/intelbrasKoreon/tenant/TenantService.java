package com.intelbrasKoreon.intelbrasKoreon.tenant;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TenantService {

    private final TenantRepository tenantRepository;

    public List<Tenant> findAll() {
        return tenantRepository.findAll();
    }

    public Tenant findById(Long id) {
        return tenantRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Tenant não encontrado: " + id));
    }

    public Tenant create(String name, String slug, String plan) {
        if (tenantRepository.existsBySlug(slug)) {
            throw new IllegalArgumentException("Slug já em uso: " + slug);
        }
        return tenantRepository.save(
                Tenant.builder().name(name).slug(slug).plan(plan).build()
        );
    }

    public Tenant setActive(Long id, boolean active) {
        Tenant t = findById(id);
        t.setActive(active);
        return tenantRepository.save(t);
    }
}
