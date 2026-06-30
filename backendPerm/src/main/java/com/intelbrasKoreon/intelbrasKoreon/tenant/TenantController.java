package com.intelbrasKoreon.intelbrasKoreon.tenant;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/tenants")
@RequiredArgsConstructor
@PreAuthorize("hasRole('SUPER_ADMIN')")
public class TenantController {

    private final TenantService tenantService;

    @GetMapping
    public List<Tenant> listAll() {
        return tenantService.findAll();
    }

    @GetMapping("/{id}")
    public Tenant getById(@PathVariable Long id) {
        return tenantService.findById(id);
    }

    @PostMapping
    public ResponseEntity<Tenant> create(@RequestBody Map<String, String> body) {
        Tenant t = tenantService.create(
                body.get("name"),
                body.get("slug"),
                body.getOrDefault("plan", "starter")
        );
        return ResponseEntity.ok(t);
    }

    @PatchMapping("/{id}/activate")
    public Tenant activate(@PathVariable Long id) {
        return tenantService.setActive(id, true);
    }

    @PatchMapping("/{id}/deactivate")
    public Tenant deactivate(@PathVariable Long id) {
        return tenantService.setActive(id, false);
    }
}
